from medcat.cdb import CDB
from medcat.utils.vocab import Vocab
from medcat.cat import CAT

import os


# todo: config file, env variables
#
class MedCatService:
    def __init__(self):
        print('Initializing MedCAT service ...')

        self.vocab = Vocab()
        self.cdb = CDB()

        self.cdb.load_dict(os.getenv("CDB_MODEL", '/Users/lroguski/__cat_models/medmen/cdb.dat'))
        self.vocab.load_dict(path=os.getenv("VOCAB_MODEL", '/Users/lroguski/__cat_models/medmen/vocab.dat'))
        self.cat = CAT(self.cdb, vocab=self.vocab)

        self.cat.spacy_cat.train = os.getenv("TRAINING_MODE", False)

        self.bulk_nproc = int(os.getenv('BULK_NPROC', 8))

        self.app_name = 'MEDCAT'
        self.app_lang = 'en'
        self.app_version = os.getenv("CAT_VERSION", '0.1.0')

        print('Service CAT is ready')


    def get_app_info(self):
        return {'name': self.app_name,
                'language': self.app_lang,
                'version': self.app_version}

    def process_content(self, content):
        if 'text' not in content:
            error_msg = "'text' field missing in the payload content."
            nlp_result = {'success': False,
                          'errors': [error_msg]}
            return nlp_result, False

        text = content['text']

        # assume an empty text or just an entry a valid content
        if text is not None and len(text) > 0:
            entities = self.cat.get_entities(text)
        else:
            entities = []

        nlp_result = {'text': text,
                      'annotations': entities,
                      'success': True
                      }

        # append the footer
        if 'footer' in content:
            nlp_result['footer'] = content['footer']

        return nlp_result, True

    def process_content_bulk(self, content):
        # prepare documents for processing -- add ids and skip blank / empty documents,
        # report error on invalid content of any of the docs in the batch
        documents = []
        content_is_valid = True
        for i in range(len(content)):
            if 'text' not in content[i]:
                content_is_valid = False

            # note that even when the text field is empty the content is considered valid
            if content[i]['text'] is not None and len(content[i]['text']) > 0:
                documents.append((i, content[i]['text']))

        if not content_is_valid:
            error_msg_field_missing = "'text' field missing in the payload content."
            nlp_results = []

            # append the error and footer for debug
            for doc in content:
                doc_result = {'success': False}
                if 'text' not in doc:
                    doc_result['errors'] = [error_msg_field_missing]

                if 'footer' in doc:
                    doc_result['footer'] = doc['footer']

                nlp_results.append(doc_result)

            return nlp_results, False

        # process all the documents
        batch_size = min(300, int(len(documents) / (2 * self.bulk_nproc)))
        res_raw = self.cat.multi_processing(documents, nproc=self.bulk_nproc, batch_size=batch_size)

        # assert len(res_raw) == len(payload['content'])
        assert len(res_raw) == len(documents)

        # parse the result -- need to sort by IDs as there's no guarantee
        # on the order of the docs processed
        res_sorted = sorted(res_raw, key=lambda x: x[0])
        nlp_results = []

        # parse the results and add footer if needed
        for i in range(len(res_sorted)):
            res = res_sorted[i]
            in_ct = content[i]

            # parse the result
            out_res = {'text': res[1]["text"],
                       'annotations': res[1]["entities"],
                       'success': True
                       }
            # append the footer
            if 'footer' in in_ct:
                out_res['footer'] = in_ct['footer']

            nlp_results.append(out_res)

        return nlp_results, True
