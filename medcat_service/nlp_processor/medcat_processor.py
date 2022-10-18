#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime, timezone
import time

import simplejson as json
from medcat.cat import CAT
from medcat.cdb import CDB
from medcat.meta_cat import MetaCAT
from medcat.vocab import Vocab


class NlpProcessor:
    """
    This class defines an interface for NLP Processor
    """
    def __init__(self):
        app_log_level = os.getenv("APP_LOG_LEVEL", logging.INFO)
        medcat_log_level = os.getenv("LOG_LEVEL", logging.INFO)

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(level=app_log_level)

        self.log.debug("APP log level set to : ", str(app_log_level))
        self.log.debug("MedCAT log level set to : ", str(medcat_log_level))

    def get_app_info(self):
        pass

    def process_content(self, content):
        pass

    def process_content_bulk(self, content):
        pass

    @staticmethod
    def _get_timestamp():
        """
        Returns the current timestamp in ISO 8601 format. Formatted as "yyyy-MM-dd"T"HH:mm:ss.SSSXXX".
        :return: timestamp string
        """
        return datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds")


class MedCatProcessor(NlpProcessor):
    """"
    MedCAT Processor class is wrapper over MedCAT that implements annotations extractions functionality
    (both single and bulk processing) that can be easily exposed for an API.
    """
    def __init__(self):
        super().__init__()

        self.log.info("Initializing MedCAT processor ...")

        self.app_name = os.getenv("APP_NAME", "MedCAT")
        self.app_lang = os.getenv("APP_MODEL_LANGUAGE", "en")
        self.app_version = MedCatProcessor._get_medcat_version()
        self.app_model = os.getenv("APP_MODEL_NAME", "unknown")
        self.entity_output_mode = os.getenv("ANNOTATIONS_ENTITY_OUTPUT_MODE", "dict").lower()

        self.cat = self._create_cat()
        self.cat.train = os.getenv("APP_TRAINING_MODE", False)

        self.bulk_nproc = int(os.getenv("APP_BULK_NPROC", 8))

        self.log.info("MedCAT processor is ready")

    def get_app_info(self):
        """
        Returns general information about the application
        :return: application information stored as KVPs
        """
        return {"service_app_name": self.app_name,
                "service_language": self.app_lang,
                "service_version": self.app_version,
                "service_model": self.app_model}

    def process_entities(self, entities):
        if type(entities) is dict:
            if "entities" in entities.keys():
                entities = entities["entities"]

            if self.entity_output_mode == "list":
                entities = list(entities.values())

        yield entities

    def process_content(self, content):
        """
        Processes a single document extracting the annotations.
        :param content: document to be processed, containing "text" field.
        :return: processing result containing document with extracted annotations stored as KVPs.
        """
        if "text" not in content:
            error_msg = "'text' field missing in the payload content."
            nlp_result = {
                          "success": False,
                          "errors": [error_msg],
                          "timestamp": NlpProcessor._get_timestamp(),
                         }

            return nlp_result

        text = content["text"]

        # assume an that a blank document is a valid document and process it only
        # when it contains any non-blank characters

        start_time_ns = time.time_ns()

        if text is not None and len(text.strip()) > 0:
            entities = self.cat.get_entities(text)
        else:
            entities = []

        elapsed_time = (time.time_ns() - start_time_ns) / 10e8  # nanoseconds to seconds

        entities = self.process_entities(entities)

        nlp_result = {
                      "text": str(text),
                      "annotations": entities,
                      "success": True,
                      "timestamp": NlpProcessor._get_timestamp(),
                      "elapsed_time":  elapsed_time
                      }

        # append the footer
        if "footer" in content:
            nlp_result["footer"] = content["footer"]

        return nlp_result

    def process_content_bulk(self, content):
        """
        Processes an array of documents extracting the annotations.
        :param content: document to be processed, containing "text" field.
        :return: processing result containing documents with extracted annotations, stored as KVPs.
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

        self.log.debug("NPROC:" + str(nproc))

        # use generators both to provide input documents and to provide resulting annotations
        # to avoid too many mem-copies
        invalid_doc_ids = []
        ann_res = []

        start_time_ns = time.time_ns()

        try:
            ann_res = self.cat.multiprocessing(
                MedCatProcessor._generate_input_doc(content, invalid_doc_ids), nproc=nproc)
        except Exception as e:
            self.log.error(repr(e))

        additional_info = {"elapsed_time": str((time.time_ns() - start_time_ns) / 10e8)}

        return self._generate_result(content, ann_res, invalid_doc_ids, additional_info)

    def retrain_medcat(self, content, replace_cdb):
        """
        Retrains Medcat and redeploys model
        """

        with open("/cat/models/data.json", "w") as f:
            json.dump(content, f)

        DATA_PATH = "/cat/models/data.json"
        CDB_PATH = "/cat/models/cdb.dat"
        VOCAB_PATH = "/cat/models/vocab.dat"

        self.log.info("Retraining Medcat Started...")

        p, r, f1, tp_dict, fp_dict, fn_dict = MedCatProcessor._retrain_supervised(self, CDB_PATH, DATA_PATH, VOCAB_PATH)

        self.log.info("Retraining Medcat Completed...")

        return {"results": [p, r, f1, tp_dict, fp_dict, fn_dict]}

    # helper MedCAT methods
    #
    def _create_cat(self):
        """
        Loads MedCAT resources and creates CAT instance
        """
        cat, cdb, vocab, config = None, None, None, None

        model_pack_path = os.getenv("APP_MEDCAT_MODEL_PACK", "").strip()
        if model_pack_path != "":
            self.log.info("Loading model pack...")
            cat = CAT.load_model_pack(model_pack_path)
            return cat
        else:
            self.log.info("APP_MEDCAT_MODEL_PACK not set, skipping....")

        # Vocabulary and Concept Database are mandatory
        if os.getenv("APP_MODEL_VOCAB_PATH", None) is None and cat is None:
            raise ValueError("Vocabulary (env: APP_MODEL_VOCAB_PATH) not specified")
        else:
            self.log.debug("Loading VOCAB ...")
            vocab = Vocab.load(os.getenv("APP_MODEL_VOCAB_PATH"))

        if os.getenv("APP_MODEL_CDB_PATH", None) is None and cat is None:
            raise Exception("Concept database (env: APP_MODEL_CDB_PATH) not specified")
        else:
            self.log.debug("Loading CDB ...")
            cdb = CDB.load(os.getenv("APP_MODEL_CDB_PATH"))

        spacy_model = os.getenv("SPACY_MODEL", "")

        if spacy_model != "":
            cdb.config.general["spacy_model"] = spacy_model
        else:
            logging.warning("SPACY_MODEL environment var not set" +
                            ", attempting to load the spacy model found within the CDB : "
                            + cdb.config.general["spacy_model"])

            if cdb.config.general["spacy_model"] == "":
                raise ValueError("No SPACY_MODEL env var declared, the CDB loaded does not have a\
                     spacy_model set in the config variable! \
                 To solve this declare the SPACY_MODEL in the env_medcat file.")

        if cat is None:
            # this is redundant as the config is already in the CDB
            config = cdb.config

        # Apply CUI filtçççer if provided
        if os.getenv("APP_MODEL_CUI_FILTER_PATH", None) is not None:
            self.log.debug("Applying CDB CUI filter ...")
            with open(os.getenv("APP_MODEL_CUI_FILTER_PATH")) as cui_file:
                all_lines = (line.rstrip() for line in cui_file)
                selected_cuis = [line for line in all_lines if line]  # filter blank lines
                cdb.filter_by_cui(selected_cuis)

        # Meta-annotation models are optional
        meta_models = []
        if os.getenv("APP_MODEL_META_PATH_LIST", None) is not None:
            self.log.debug("Loading META annotations ...")
            for model_path in os.getenv("APP_MODEL_META_PATH_LIST").split(":"):
                m = MetaCAT.load(model_path)
                meta_models.append(m)

        if cat:
            meta_models.extend(cat._meta_cats)

        config.general["log_level"] = os.getenv("LOG_LEVEL", logging.INFO)

        cat = CAT(cdb=cdb, config=config, vocab=vocab, meta_cats=meta_models)

        return cat

    # helper generator functions to avoid multiple copies of data
    #
    @staticmethod
    def _generate_input_doc(documents, invalid_doc_idx):
        """
            Generator function returning documents to be processed as a list of tuples:
            (idx, text), (idx, text), ...
            Skips empty documents and reports their ids to the invalid_doc_idx array
            :param documents: array of input documents that contain "text" field
            :param invalid_doc_idx:  array that will contain invalid document idx
            :return: consecutive tuples of (idx, document)
        """
        for i in range(0, len(documents)):
            # assume the document to be processed only when it is not blank
            if documents[i] is not None and "text" in documents[i] and documents[i]["text"] is not None \
                    and len(documents[i]["text"].strip()) > 0:
                yield i, documents[i]["text"]
            else:
                invalid_doc_idx.append(i)

    def _generate_result(self, in_documents, annotations, invalid_doc_idx, additional_info={}):
        """
            Generator function merging the resulting annotations with the input documents.
            The result for documents that were invalid will not contain any annotations.
            :param in_documents: array of input documents that contain "text" field
            :param annotations: array of annotations extracted from documents
            :param invalid_doc_idx: array of invalid document idx
            :return:
        """

        # generate output for valid annotations
        for i in range(len(annotations)):
            in_ct = in_documents[i]

            entities = self.process_entities(annotations[i])

            # parse the result
            out_res = {"text": str(in_documents[i]["text"]),
                       "annotations": entities,
                       "success": True,
                       "timestamp": NlpProcessor._get_timestamp(),
                       }
            out_res.update(additional_info)
            # append the footer
            if "footer" in in_ct:
                out_res["footer"] = in_ct["footer"]

            yield out_res

        # generate output for invalid documents
        for i in invalid_doc_idx:
            in_ct = in_documents[i]

            out_res = {"text": in_ct["text"],
                       "annotations": [],
                       "success": True,
                       "timestamp": NlpProcessor._get_timestamp()
                       }
            # append the footer
            if "footer" in in_ct:
                out_res["footer"] = in_ct["footer"]

            yield out_res

    @staticmethod
    def _get_medcat_version():
        """
        Returns the version string of the MedCAT module as reported by pip
        :return:
        """
        try:
            import pkg_resources
            version = pkg_resources.require("medcat")[0].version
            return str(version)
        except Exception:
            raise Exception("Cannot read the MedCAT library version")

    def _retrain_supervised(self, cdb_path, data_path, vocab_path, cv=1, nepochs=1,
                            test_size=0.1, lr=1, groups=None, **kwargs):

        data = json.load(open(data_path))
        correct_ids = self._prepareDocumentsForPeformanceAnalysis(data)

        cat = MedCatProcessor._create_cat(self)

        f1_base = MedCatProcessor._computeF1forDocuments(self, data, self.cat, correct_ids)[2]
        self.log.info("Base model F1: " + str(f1_base))

        cat.train = True
        cat.spacy_cat.MIN_ACC = os.getenv("MIN_ACC", 0.20)
        cat.spacy_cat.MIN_ACC_TH = os.getenv("MIN_ACC_TH", 0.20)

        self.log.info("Starting supervised training...")

        try:
            cat.train_supervised(data_path=data_path, lr=1, test_size=0.1, use_groups=None, nepochs=3)
        except Exception:
            self.log.info("Did not complete all supervised training")

        p, r, f1, tp_dict, fp_dict, fn_dict = MedCatProcessor._computeF1forDocuments(self, data, cat, correct_ids)

        self.log.info("Trained model F1: " + str(f1))

        if MedCatProcessor._checkmodelimproved(f1, f1_base):
            self.log.info("Model will be saved...")

            cat.cdb.save_dict("/cat/models/cdb_new.dat")

        self.log.info("Completed Retraining Medcat...")
        return p, r, f1, tp_dict, fp_dict, fn_dict

    def _computeF1forDocuments(self, data, cat, correct_ids):

        true_positives_dict, false_positives_dict, false_negatives_dict = {}, {}, {}
        true_positive_no, false_positive_no, false_negative_no = 0, 0, 0

        for project in data["projects"]:

            predictions = {}
            documents = project["documents"]
            true_positives_dict[project["id"]] = {}
            false_positives_dict[project["id"]] = {}
            false_negatives_dict[project["id"]] = {}

            for document in documents:
                true_positives_dict[project["id"]][document["id"]] = {}
                false_positives_dict[project["id"]][document["id"]] = {}
                false_negatives_dict[project["id"]][document["id"]] = {}

                results = cat.get_entities(document["text"])
                predictions[document["id"]] = [[a["start"], a["end"], a["cui"]] for a in results]

                tps, fps, fns = self._getAccuraciesforDocument(correct_ids[project["id"]][document["id"]],
                                                               predictions[document["id"]])
                true_positive_no += len(tps)
                false_positive_no += len(fps)
                false_negative_no += len(fns)

                true_positives_dict[project["id"]][document["id"]] = tps
                false_positives_dict[project["id"]][document["id"]] = fps
                false_negatives_dict[project["id"]][document["id"]] = fns

        if (true_positive_no + false_positive_no) == 0:
            precision = 0
        else:
            precision = true_positive_no / (true_positive_no + false_positive_no)
        if (true_positive_no + false_negative_no) == 0:
            recall = 0
        else:
            recall = true_positive_no / (true_positive_no + false_negative_no)
        if (precision + recall) == 0:
            f1 = 0
        else:
            f1 = 2*((precision*recall) / (precision + recall))

        return precision, recall, f1, true_positives_dict, false_positives_dict, false_negatives_dict

    @staticmethod
    def _prepareDocumentsForPeformanceAnalysis(data):
        correct_ids = {}
        for project in data["projects"]:
            correct_ids[project["id"]] = {}

            for document in project["documents"]:
                for entry in document["annotations"]:
                    if entry["correct"]:
                        if document["id"] not in correct_ids[project["id"]]:
                            correct_ids[project["id"]][document["id"]] = []
                        correct_ids[project["id"]][document["id"]].append([entry["start"], entry["end"], entry["cui"]])

        return correct_ids

    @staticmethod
    def _getAccuraciesforDocument(prediction, correct_ids):

        tup1 = list(map(tuple, correct_ids))
        tup2 = list(map(tuple, prediction))

        true_positives = list(map(list, set(tup1).intersection(tup2)))
        false_positives = list(map(list, set(tup1).difference(tup2)))
        false_negatives = list(map(list, set(tup2).difference(tup1)))

        return true_positives, false_positives, false_negatives

    @staticmethod
    def _checkmodelimproved(f1_model_a, f1_model_b):

        if f1_model_a > f1_model_b:
            return True
        else:
            return False
