#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os, json
from datetime import datetime, timezone

from medcat.cat import CAT
from medcat.cdb import CDB
from medcat.meta_cat import MetaCAT
from medcat.utils.vocab import Vocab
from medcat.utils.helpers import run_cv
import numpy as np

class NlpProcessor:
    """
    This class defines an interface for NLP Processor
    """
    def __init__(self): 
        self.log = logging.getLogger(self.__class__.__name__)

    def get_app_info(self):
        pass

    def process_content(self, content):
        pass

    def process_content_bulk(self, content):
        pass

    @staticmethod
    def _get_timestamp():
        """
        Returns the current timestamp in ISO 8601 format. Formatted as "yyyy-MM-dd'T'HH:mm:ss.SSSXXX".
        :return: timestamp string
        """
        return datetime.now(tz=timezone.utc).isoformat(timespec='milliseconds')


class MedCatProcessor(NlpProcessor):
    """"
    MedCAT Processor class is wrapper over MedCAT that implements annotations extractions functionality
    (both single and bulk processing) that can be easily exposed for an API.
    """
    def __init__(self):
        super().__init__()

        self.log.info('Initializing MedCAT processor ...')

        # TODO: use a config file instead of env variables
        #
        self.app_name = 'MedCAT'
        self.app_lang = 'en'
        self.app_version = MedCatProcessor._get_medcat_version()
        self.app_model = os.getenv("APP_MODEL_NAME", 'unknown')

        self.cat = self._create_cat()
        self.cat.spacy_cat.train = os.getenv("APP_TRAINING_MODE", False)

        self.bulk_nproc = int(os.getenv('APP_BULK_NPROC', 8))

        self.log.info('MedCAT processor is ready')

    def get_app_info(self):
        """
        Returns general information about the application
        :return: application information stored as KVPs
        """
        return {'name': self.app_name,
                'language': self.app_lang,
                'version': self.app_version,
                'model': self.app_model}

    def process_content(self, content):
        """
        Processes a single document extracting the annotations.
        :param content: document to be processed, containing 'text' field.
        :return: processing result containing document with extracted annotations stored as KVPs.
        """
        if 'text' not in content:
            error_msg = "'text' field missing in the payload content."
            nlp_result = {'success': False,
                          'errors': [error_msg],
                          'timestamp': NlpProcessor._get_timestamp()
                          }
            return nlp_result, False

        text = content['text']

        # assume an that a blank document is a valid document and process it only
        # when it contains any non-blank characters
        if text is not None and len(text.strip()) > 0:
            entities = self.cat.get_entities(text)
        else:
            entities = []

        nlp_result = {'text': text,
                      'annotations': entities,
                      'success': True,
                      'timestamp': NlpProcessor._get_timestamp()
                      }

        # append the footer
        if 'footer' in content:
            nlp_result['footer'] = content['footer']

        return nlp_result

    def process_content_bulk(self, content):
        """
        Processes an array of documents extracting the annotations.
        :param content: document to be processed, containing 'text' field.
        :return: processing result containing documents with extracted annotations,stored as KVPs.
        """

        # process at least 10 docs per thread and don't bother with starting
        # additional threads when less documents were provided
        min_doc_per_thread = 10
        num_slices = max(1, int(len(content) / min_doc_per_thread))
        batch_size = min(300, num_slices)

        if batch_size >= self.bulk_nproc:
            nproc = self.bulk_nproc
        else:
            batch_size = min_doc_per_thread
            nproc = max(1, num_slices)
            if len(content) > batch_size * nproc:
                nproc += 1

        # use generators both to provide input documents and to provide resulting annotations
        # to avoid too many mem-copies
        invalid_doc_ids = []
        ann_res = self.cat.multi_processing(MedCatProcessor._generate_input_doc(content, invalid_doc_ids),
                                            nproc=nproc, batch_size=batch_size)

        return MedCatProcessor._generate_result(content, ann_res, invalid_doc_ids)


    def retrain_medcat(self, content, replace_cdb):
        """
        Retrains Medcat and redeploys model
        """

        with open('/cat/models/data.json', 'w') as f:
            json.dump(content, f)
        
        DATA_PATH = '/cat/models/data.json'
        CDB_PATH = '/cat/models/cdb.dat'
        VOCAB_PATH = '/cat/models/vocab.dat'

        self.log.info('Retraining Medcat Started...')

        fps, fns, tps, ps, rs, f1s, cui_counts = MedCatProcessor._run_cv(self, CDB_PATH, DATA_PATH, VOCAB_PATH)

        self.log.info('Retraining Medcat Completed...')

            
        return {'results': [fps, fns, tps, ps, rs, f1s, cui_counts]}



    # helper MedCAT methods
    #
    def _create_cat(self):
        """
        Loads MedCAT resources and creates CAT instance
        """
        if os.getenv("APP_MODEL_VOCAB_PATH") is None:
            raise ValueError("Vocabulary (env: APP_MODEL_VOCAB_PATH) not specified")

        if os.getenv("APP_MODEL_CDB_PATH") is None:
            raise Exception("Concept database (env: APP_MODEL_CDB_PATH) not specified")

        # Vocabulary and Concept Database are mandatory
        vocab = Vocab()
        vocab.load_dict(path=os.getenv("APP_MODEL_VOCAB_PATH"))

        cdb = CDB()
        cdb.load_dict(path=os.getenv("APP_MODEL_CDB_PATH"))

        # Meta-annotation models are optional
        meta_models = []
        if os.getenv("APP_MODEL_META_PATH_LIST") is not None:
            for model_path in os.getenv("APP_MODEL_META_PATH_LIST").split(':'):
                m = MetaCAT(save_dir=model_path)
                m.load()
                meta_models.append(m)

        return CAT(cdb=cdb, vocab=vocab, meta_cats=meta_models)

    # helper generator functions to avoid multiple copies of data
    #
    @staticmethod
    def _generate_input_doc(documents, invalid_doc_idx):
        """
        Generator function returning documents to be processed as a list of tuples:
          (idx, text), (idx, text), ...
        Skips empty documents and reports their ids to the invalid_doc_idx array
        :param documents: array of input documents that contain 'text' field
        :param invalid_doc_idx:  array that will contain invalid document idx
        :return: consecutive tuples of (idx, document)
        """
        for i in range(0, len(documents)):
            # assume the document to be processed only when it is not blank
            if 'text' in documents[i] and documents[i]['text'] is not None and len(documents[i]['text'].strip()) > 0:
                yield i, documents[i]['text']
            else:
                invalid_doc_idx.append(i)

    @staticmethod
    def _generate_result(in_documents, annotations, invalid_doc_idx):
        """
        Generator function merging the resulting annotations with the input documents.
        The result for documents that were invalid will not contain any annotations.
        :param in_documents: array of input documents that contain 'text' field
        :param annotations: array of annotations extracted from documents
        :param invalid_doc_idx: array of invalid document idx
        :return:
        """
        # generate output for valid annotations
        for i in range(len(annotations)):
            res = annotations[i]
            res_idx = res[0]
            in_ct = in_documents[res_idx]

            # parse the result
            out_res = {'text': res[1]["text"],
                       'annotations': res[1]["entities"],
                       'success': True,
                       'timestamp': NlpProcessor._get_timestamp()
                       }
            # append the footer
            if 'footer' in in_ct:
                out_res['footer'] = in_ct['footer']

            yield out_res

        # generate output for invalid documents
        for i in invalid_doc_idx:
            in_ct = in_documents[i]

            out_res = {'text': in_ct["text"],
                       'annotations': [],
                       'success': True,
                       'timestamp': NlpProcessor._get_timestamp()
                       }
            # append the footer
            if 'footer' in in_ct:
                out_res['footer'] = in_ct['footer']

            yield out_res

    @staticmethod
    def _get_medcat_version():
        """
        Returns the version string of the MedCAT module as reported by pip
        :return:
        """
        try:
            import subprocess
            result = subprocess.check_output(['pip', 'show', 'medcat'], universal_newlines=True)
            version_line = list(filter(lambda v: 'Version' in v, result.split('\n')))
            return version_line[0].split(' ')[1]
        except Exception:
            raise Exception("Cannot read the MedCAT library version")

    
    def _run_cv(self, cdb_path, data_path, vocab_path, cv=1, nepochs=1, test_size=0.1, lr=1, groups=None, **kwargs):

        f1s, ps, rs, tps, fns, fps, cui_counts = {}, {}, {}, {}, {}, {}, {}
        
        data = json.load(open(data_path))
        correct_ids = MedCatProcessor._prepareDocumentsForPeformanceAnalysis(data)

        cdb = CDB()
        cdb.load_dict(cdb_path)
        vocab = Vocab()
        vocab.load_dict(path=vocab_path)
        starting_cat = CAT(cdb, vocab=vocab)

        current_best_f1 = MedCatProcessor._computeF1forDocuments(self, data, starting_cat, correct_ids)


        use_groups = False
        if groups is not None:
            use_groups = True

        for _ in range(cv):
            cdb = CDB()
            cdb.load_dict(cdb_path)
            vocab = Vocab()
            vocab.load_dict(path=vocab_path)
            cat = CAT(cdb, vocab=vocab)
            cat.train = False
            cat.spacy_cat.MIN_ACC = 0.30
            cat.spacy_cat.MIN_ACC_TH = 0.30

            # Add groups if they exist
            if groups is not None:
                for cui in cdb.cui2info.keys():
                    if "group" in cdb.cui2info[cui]:
                        del cdb.cui2info[cui]['group']
                groups = json.load(open("./groups.json"))
                for k,v in groups.items():
                    for val in v:
                        cat.add_cui_to_group(val, k)


            fp, fn, tp, p, r, f1, cui_counts, examples = cat.train_supervised(data_path=data_path, reset_cdb=True,
                                lr=1, test_size=test_size, use_groups=use_groups, nepochs=nepochs, **kwargs)

            for key in f1.keys():
                if key in f1s:
                    f1s[key].append(f1[key])
                else:
                    f1s[key] = [f1[key]]

                if key in ps:
                    ps[key].append(p[key])
                else:
                    ps[key] = [p[key]]

                if key in rs:
                    rs[key].append(r[key])
                else:
                    rs[key] = [r[key]]

                if key in tps:
                    tps[key].append(tp.get(key, 0))
                else:
                    tps[key] = [tp.get(key, 0)]

                if key in fps:
                    fps[key].append(fp.get(key, 0))
                else:
                    fps[key] = [fp.get(key, 0)]

                if key in fns:
                    fns[key].append(fn.get(key, 0))
                else:
                    fns[key] = [fn.get(key, 0)]

            f1_documents = MedCatProcessor._computeF1forDocuments(self, data, cat, correct_ids)    
            self.log.info('Previous F1: ' + str(current_best_f1))
            self.log.info('New F1: ' + str(f1_documents))

            self.log.info('Determing if medcat will be replaced...')

            if MedCatProcessor._checkmodelimproved(f1_documents, current_best_f1):
                self.log.info('Model will be replaced...')  
                current_best_f1 = f1_documents

                try:
                    cat.cdb.save_dict('/cat/models/cdb_new.dat')
                except Exception as e:
                    return Response(response="Internal processing error %s" % e, status=500)

        self.log.info('Retraining Medcat Returning now...')
        return fps, fns, tps, ps, rs, f1s, cui_counts

    
    def _computeF1forDocuments(self, data, cat, correct_ids):
        
        self.log.info('Computing f1s')
        predictions = {}
        for document in data['projects'][0]['documents']:
            results = cat.get_entities(document['text'])
            predictions[document['id']] = [[a['start'], a['end']] for a in results]

        predictions_counts = np.sum([len(prediction) for prediction in predictions.values()])
        ground_counts = np.sum([len(ground) for ground in correct_ids.values()])

        true_positives_documents = 0
        for correct_id_key in correct_ids.keys():
            if correct_id_key in predictions.keys():
                A = np.array(correct_ids[correct_id_key])
                B = np.array(predictions[correct_id_key])
                
                aset = set([tuple(x) for x in A])
                bset = set([tuple(x) for x in B])
                true_positives_documents += np.array([x for x in aset & bset]).shape[0]

                
        false_positives_documents = predictions_counts - true_positives_documents
        false_negative_documents = ground_counts - true_positives_documents

        if (true_positives_documents + false_positives_documents) == 0:
            precision_documents = 0
        else:
            precision_documents = (true_positives_documents) / (true_positives_documents + false_positives_documents)

        if (true_positives_documents + false_negative_documents) == 0:
            recall_documents = 0
        else:
            recall_documents = (true_positives_documents) / (true_positives_documents + false_negative_documents)

        if (precision_documents + recall_documents) == 0:
            f1_documents = 0
        else:
            f1_documents = 2*((precision_documents*recall_documents)/ precision_documents + recall_documents)
        return f1_documents


    @staticmethod
    def _prepareDocumentsForPeformanceAnalysis(data):
        
        correct_ids = {}
        for document in data['projects'][0]['documents']:
            for entry in document['annotations']:
                if entry['correct'] == True:
                    if document['id'] not in correct_ids:
                        correct_ids[document['id']] = []
                    correct_ids[document['id']].append([entry['start'], entry['end']])

        return correct_ids

    @staticmethod
    def _checkmodelimproved(f1_model_a, f1_model_b):

        if f1_model_a > f1_model_b:
            return True
        else:
            return False
