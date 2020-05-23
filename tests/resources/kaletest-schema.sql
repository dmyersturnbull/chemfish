

-- Host: 127.0.0.1    Database: valartest
-- ------------------------------------------------------
-- Server version    10.3.20-MariaDB-0ubuntu0.19.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `annotations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `annotations` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `value` varchar(255) DEFAULT NULL,
  `level` enum('0:good','1:note','2:caution','3:warning','4:danger','9:deleted','to_fix','fixed') NOT NULL DEFAULT '1:note',
  `run_id` mediumint(8) unsigned DEFAULT NULL,
  `submission_id` mediumint(8) unsigned DEFAULT NULL,
  `well_id` mediumint(8) unsigned DEFAULT NULL,
  `assay_id` smallint(5) unsigned DEFAULT NULL,
  `annotator_id` smallint(5) unsigned NOT NULL,
  `description` mediumtext DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `concern_to_run` (`run_id`),
  KEY `concern_to_well` (`well_id`),
  KEY `concern_to_assay` (`assay_id`),
  KEY `concern_to_person` (`annotator_id`),
  KEY `level` (`level`),
  KEY `name` (`name`),
  KEY `concern_to_submission` (`submission_id`),
  KEY `value` (`value`),
  CONSTRAINT `annotation_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `concern_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `concern_to_person` FOREIGN KEY (`annotator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `concern_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `concern_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `api_keys`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `api_keys` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `value` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assay_params`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assay_params` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `assay_id` smallint(5) unsigned NOT NULL,
  `name` varchar(30) CHARACTER SET latin1 NOT NULL,
  `value` double NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assay_and_name_unique` (`name`,`assay_id`),
  KEY `assay_param_to_assay` (`assay_id`),
  KEY `value` (`value`),
  CONSTRAINT `assay_param_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assay_positions`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assay_positions` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `battery_id` smallint(5) unsigned NOT NULL,
  `assay_id` smallint(5) unsigned NOT NULL,
  `start` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `protocol_assay_start_unique` (`battery_id`,`assay_id`,`start`),
  KEY `protocol_id` (`battery_id`),
  KEY `assay_id` (`assay_id`),
  KEY `start` (`start`),
  CONSTRAINT `assay_in_protocol_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`),
  CONSTRAINT `assay_in_protocol_to_protocol` FOREIGN KEY (`battery_id`) REFERENCES `batteries` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `assays`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `assays` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(250) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `length` int(10) unsigned NOT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT 0,
  `template_assay_id` smallint(5) unsigned DEFAULT NULL,
  `frames_sha1` binary(20) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_frames_sha1_unique` (`name`,`frames_sha1`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `name` (`name`),
  KEY `hash` (`frames_sha1`) USING BTREE,
  KEY `assay_to_template_assay` (`template_assay_id`),
  CONSTRAINT `assay_to_template_assay` FOREIGN KEY (`template_assay_id`) REFERENCES `template_assays` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `audio_files`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `audio_files` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `filename` varchar(100) NOT NULL,
  `notes` varchar(250) DEFAULT NULL,
  `n_seconds` double unsigned NOT NULL,
  `data` mediumblob NOT NULL,
  `sha1` binary(20) NOT NULL,
  `creator_id` smallint(5) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `filename_unique` (`filename`),
  UNIQUE KEY `sha1_unique` (`sha1`),
  KEY `creator_id` (`creator_id`),
  CONSTRAINT `audio_file_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `batch_annotations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `batch_annotations` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `level` enum('0:good','1:note','2:caution','3:warning','4:danger','9:deleted') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '1:note',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `value` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `annotator_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `batch_concern_to_batch` (`batch_id`),
  KEY `batch_concern_to_user` (`annotator_id`),
  KEY `level` (`level`),
  KEY `name` (`name`),
  KEY `value` (`value`),
  CONSTRAINT `batch_concern_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE CASCADE,
  CONSTRAINT `batch_concern_to_user` FOREIGN KEY (`annotator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `batch_labels`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `batch_labels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `name` varchar(250) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `external_id` (`name`),
  KEY `data_source_id_2` (`ref_id`),
  KEY `ordered_compound_id_2` (`batch_id`),
  CONSTRAINT `id_to_ordered_compound` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE CASCADE,
  CONSTRAINT `oc_id_to_data_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `batches`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `batches` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `lookup_hash` varchar(14) NOT NULL,
  `tag` varchar(100) DEFAULT NULL,
  `compound_id` mediumint(8) unsigned DEFAULT NULL,
  `made_from_id` mediumint(8) unsigned DEFAULT NULL,
  `supplier_id` smallint(5) unsigned DEFAULT NULL,
  `ref_id` smallint(5) unsigned DEFAULT NULL,
  `legacy_internal_id` varchar(255) DEFAULT NULL,
  `location_id` smallint(5) unsigned DEFAULT NULL,
  `box_number` smallint(5) unsigned DEFAULT NULL,
  `well_number` smallint(5) unsigned DEFAULT NULL,
  `location_note` varchar(20) DEFAULT NULL,
  `amount` varchar(100) DEFAULT NULL,
  `concentration_millimolar` double unsigned DEFAULT NULL,
  `solvent_id` mediumint(8) unsigned DEFAULT NULL,
  `molecular_weight` double unsigned DEFAULT NULL,
  `supplier_catalog_number` varchar(20) DEFAULT NULL,
  `person_ordered` smallint(5) unsigned DEFAULT NULL,
  `date_ordered` date DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `suspicious` tinyint(1) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_hash` (`lookup_hash`),
  UNIQUE KEY `box_number_well_number` (`box_number`,`well_number`),
  UNIQUE KEY `tag_unique` (`tag`),
  KEY `compound_id` (`compound_id`),
  KEY `solvent_id` (`solvent_id`),
  KEY `internal_id` (`legacy_internal_id`) USING BTREE,
  KEY `ordered_compound_to_external_source` (`ref_id`),
  KEY `ordered_compound_to_user` (`person_ordered`),
  KEY `ordered_compound_to_compound_source` (`supplier_id`),
  KEY `date_ordered` (`date_ordered`),
  KEY `box_number` (`box_number`),
  KEY `well_number` (`well_number`),
  KEY `batch_to_batch` (`made_from_id`),
  KEY `batch_to_location` (`location_id`),
  CONSTRAINT `batch_to_batch` FOREIGN KEY (`made_from_id`) REFERENCES `batches` (`id`),
  CONSTRAINT `batch_to_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`),
  CONSTRAINT `batch_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
  CONSTRAINT `ordered_compound_to_external_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `ordered_compound_to_solvent` FOREIGN KEY (`solvent_id`) REFERENCES `compounds` (`id`),
  CONSTRAINT `ordered_compound_to_user` FOREIGN KEY (`person_ordered`) REFERENCES `users` (`id`),
  CONSTRAINT `ordered_compounds_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `batteries`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `batteries` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `length` int(10) unsigned NOT NULL,
  `author_id` smallint(5) unsigned DEFAULT NULL,
  `template_id` smallint(5) unsigned DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT 0,
  `notes` TEXT DEFAULT NULL,
  `assays_sha1` binary(20) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `creator_id` (`author_id`),
  KEY `protocol_to_template` (`template_id`),
  KEY `length` (`length`),
  KEY `assays_sha1` (`assays_sha1`),
  CONSTRAINT `protocol_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `biomarker_experiments`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `biomarker_experiments` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `tag` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(250) COLLATE utf8mb4_unicode_ci NOT NULL,
  `kind` enum('ms','rna-seq','imaging','other') COLLATE utf8mb4_unicode_ci NOT NULL,
  `experimentalist_id` smallint(5) unsigned NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `datetime_prepared` datetime NOT NULL,
  `datetime_collected` datetime NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag_unique` (`tag`),
  KEY `biomarker_experiment_to_user` (`experimentalist_id`),
  KEY `biomarker_experiment_to_ref` (`ref_id`),
  CONSTRAINT `biomarker_experiment_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `biomarker_experiment_to_user` FOREIGN KEY (`experimentalist_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `biomarker_levels`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `biomarker_levels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `sample_id` smallint(5) unsigned NOT NULL,
  `biomarker_id` int(10) unsigned NOT NULL,
  `tissue_id` smallint(5) unsigned DEFAULT NULL,
  `fold_change` double unsigned DEFAULT NULL,
  `full_value` varchar(250) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `biomarker_level_to_biomarker` (`biomarker_id`),
  KEY `biomarker_level_to_sample` (`sample_id`),
  CONSTRAINT `biomarker_level_to_biomarker` FOREIGN KEY (`biomarker_id`) REFERENCES `biomarkers` (`id`),
  CONSTRAINT `biomarker_level_to_sample` FOREIGN KEY (`sample_id`) REFERENCES `biomarker_samples` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `biomarker_samples`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `biomarker_samples` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `experiment_id` smallint(5) unsigned NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `control_type_id` tinyint(3) unsigned NOT NULL,
  `from_well_id` mediumint(8) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_experiment_unique` (`name`,`experiment_id`),
  KEY `biomarker_sample_to_biomarker_experiment` (`experiment_id`),
  KEY `biomarker_sample_to_well` (`from_well_id`),
  KEY `biomarker_sample_to_control_type` (`control_type_id`),
  CONSTRAINT `biomarker_sample_to_biomarker_experiment` FOREIGN KEY (`experiment_id`) REFERENCES `biomarker_experiments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `biomarker_sample_to_control_type` FOREIGN KEY (`control_type_id`) REFERENCES `control_types` (`id`),
  CONSTRAINT `biomarker_sample_to_well` FOREIGN KEY (`from_well_id`) REFERENCES `wells` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `biomarker_treatments`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `biomarker_treatments` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `sample_id` smallint(5) unsigned NOT NULL,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `micromolar_dose` double unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sample_batch_unique` (`sample_id`,`batch_id`),
  KEY `biomarker_treatment_to_batch` (`batch_id`),
  CONSTRAINT `biomarker_treatment_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`),
  CONSTRAINT `biomarker_treatment_to_sample` FOREIGN KEY (`sample_id`) REFERENCES `biomarker_samples` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `biomarkers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `biomarkers` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(250) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_gene_id` mediumint(8) unsigned DEFAULT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `biomarker_to_gene` (`is_gene_id`),
  KEY `biomarker_to_ref` (`ref_id`),
  CONSTRAINT `biomarker_to_gene` FOREIGN KEY (`is_gene_id`) REFERENCES `genes` (`id`) ON DELETE SET NULL,
  CONSTRAINT `biomarker_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `compound_labels`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `compound_labels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `compound_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(1000) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `compound_id` (`compound_id`),
  KEY `compound_name_to_external_source` (`ref_id`),
  CONSTRAINT `compound_name_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `compound_name_to_external_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `compound_links`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `compound_links` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `child_id` mediumint(8) unsigned NOT NULL,
  `parent_id` mediumint(8) unsigned NOT NULL,
  `kind` enum('salt','stero','both','neither') COLLATE utf8mb4_unicode_ci NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL DEFAULT 1,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `child_parent_kind_unique` (`child_id`,`parent_id`,`kind`),
  KEY `compound_link_to_parent` (`parent_id`),
  KEY `compound_link_to_ref` (`ref_id`),
  CONSTRAINT `compound_link_to_child` FOREIGN KEY (`child_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `compound_link_to_parent` FOREIGN KEY (`parent_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `compound_link_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `compounds`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `compounds` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `inchi` varchar(2000) NOT NULL,
  `inchikey` char(27) NOT NULL,
  `inchikey_connectivity` char(14) NOT NULL,
  `chembl_id` varchar(20) DEFAULT NULL,
  `chemspider_id` int(10) unsigned DEFAULT NULL,
  `smiles` varchar(2000) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `inchikey` (`inchikey`) USING BTREE,
  KEY `inchikey_connectivity` (`inchikey_connectivity`),
  KEY `chembl_id` (`chembl_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `config_files`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `config_files` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `toml_text` mediumtext NOT NULL,
  `text_sha1` binary(20) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `text_sha1_unique` (`text_sha1`),
  KEY `text_sha1` (`text_sha1`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `control_types`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `control_types` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(250) NOT NULL,
  `positive` tinyint(1) NOT NULL,
  `drug_related` tinyint(1) NOT NULL DEFAULT 1,
  `genetics_related` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `name` (`name`),
  KEY `positive` (`positive`),
  KEY `drug_related` (`drug_related`),
  KEY `genetics_related` (`genetics_related`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dags_to_create`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dags_to_create` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `submission_hash` char(12) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `dag_created` tinyint(1) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  `feature_type` tinyint(3) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_hash_hex_feature` (`submission_hash`,`feature_type`),
  KEY `feature_type` (`feature_type`),
  CONSTRAINT `dags_to_create_ibfk_1` FOREIGN KEY (`feature_type`) REFERENCES `features` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `experiment_tags`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `experiment_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `experiment_id` smallint(5) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(255) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `exp_tag_unique` (`experiment_id`,`name`),
  KEY `experiment_tag_to_ref` (`ref_id`),
  CONSTRAINT `experiment_tag_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `tag_to_experiment` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `experiments`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `experiments` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `project_id` smallint(5) unsigned NOT NULL,
  `battery_id` smallint(5) unsigned NOT NULL,
  `template_plate_id` smallint(5) unsigned DEFAULT NULL,
  `transfer_plate_id` smallint(5) unsigned DEFAULT NULL,
  `default_acclimation_sec` smallint(5) unsigned NOT NULL,
  `notes` text DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT 1,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `protocol_id` (`battery_id`),
  KEY `project_to_superproject` (`project_id`),
  KEY `project_to_template_plate` (`template_plate_id`),
  KEY `experiment_to_transfer_plate` (`transfer_plate_id`),
  KEY `experiment_to_user` (`creator_id`),
  CONSTRAINT `experiment_to_transfer_plate` FOREIGN KEY (`transfer_plate_id`) REFERENCES `transfer_plates` (`id`),
  CONSTRAINT `experiment_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `project_to_protocol` FOREIGN KEY (`battery_id`) REFERENCES `batteries` (`id`),
  CONSTRAINT `project_to_superproject` FOREIGN KEY (`project_id`) REFERENCES `superprojects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `project_to_template_plate` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `features`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `features` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) NOT NULL,
  `dimensions` varchar(20) NOT NULL,
  `data_type` enum('byte','short','int','float','double','unsigned_byte','unsigned_short','unsigned_int','unsigned_float','unsigned_double','utf8_char') NOT NULL DEFAULT 'float',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gene_labels`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gene_labels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `gene_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_gene_source_unique` (`gene_id`,`name`,`ref_id`),
  KEY `gene` (`gene_id`),
  KEY `name` (`name`),
  KEY `ref` (`ref_id`),
  CONSTRAINT `gene_name_to_gene` FOREIGN KEY (`gene_id`) REFERENCES `genes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `gene_name_to_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDBDEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genes`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genes` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(30) DEFAULT NULL,
  `pub_link` varchar(255) DEFAULT NULL,
  `description` varchar(250) DEFAULT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `user_id` smallint(5) unsigned NOT NULL,
  `raw_file` blob DEFAULT NULL,
  `raw_file_sha1` binary(20) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `name` (`name`),
  KEY `pub_link` (`pub_link`),
  KEY `gene_to_ref` (`ref_id`),
  KEY `gene_to_user` (`user_id`),
  CONSTRAINT `gene_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `gene_to_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genetic_construct_features`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genetic_construct_features` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `kind` varchar(50) NOT NULL,
  `name` varchar(250) NOT NULL,
  `gene_id` mediumint(8) unsigned DEFAULT NULL,
  `construct_id` smallint(5) unsigned NOT NULL,
  `start` bigint(20) DEFAULT NULL,
  `end` bigint(20) DEFAULT NULL,
  `is_complement` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gene_construct_unique` (`gene_id`,`construct_id`),
  KEY `to_construct` (`construct_id`),
  CONSTRAINT `to_construct` FOREIGN KEY (`construct_id`) REFERENCES `genetic_constructs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `to_gene` FOREIGN KEY (`gene_id`) REFERENCES `genes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genetic_constructs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genetic_constructs` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `kind` enum('plasmid','guide','morpholino','other') NOT NULL,
  `name` varchar(100) NOT NULL,
  `location_id` smallint(5) unsigned DEFAULT NULL,
  `box_number` smallint(5) unsigned NOT NULL,
  `tube_number` smallint(5) unsigned NOT NULL,
  `description` varchar(250) NOT NULL,
  `supplier_id` smallint(5) unsigned DEFAULT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `pmid` varchar(30) DEFAULT NULL,
  `pub_link` varchar(150) DEFAULT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `date_made` datetime DEFAULT NULL,
  `selection_marker` varchar(50) DEFAULT NULL,
  `bacterial_strain` varchar(50) DEFAULT NULL,
  `vector` varchar(50) DEFAULT NULL,
  `raw_file` blob DEFAULT NULL,
  `raw_file_sha1` binary(20) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `box_tube_unique` (`box_number`,`tube_number`),
  UNIQUE KEY `name_unique` (`name`),
  UNIQUE KEY `ape_file_sha1_unique` (`raw_file_sha1`),
  KEY `plasmid_to_user` (`creator_id`),
  KEY `genetic_construct_to_location` (`location_id`),
  KEY `box_number` (`box_number`),
  KEY `tube_number` (`tube_number`),
  KEY `bacterial_strain` (`bacterial_strain`),
  KEY `raw_file_sha1` (`raw_file_sha1`),
  KEY `date_made` (`date_made`),
  KEY `kind` (`kind`),
  KEY `vector` (`vector`),
  KEY `pmid` (`pmid`),
  KEY `construct_to_supplier` (`supplier_id`),
  KEY `genetic_construct_to_ref` (`ref_id`),
  CONSTRAINT `construct_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
  CONSTRAINT `genetic_construct_to_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`),
  CONSTRAINT `genetic_construct_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `plasmid_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genetic_events`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genetic_events` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `variant_id` mediumint(8) unsigned DEFAULT NULL,
  `gene_id` mediumint(8) unsigned DEFAULT NULL,
  `description` varchar(250) DEFAULT NULL,
  `injection_mix` varchar(100) DEFAULT NULL,
  `user_id` smallint(5) unsigned NOT NULL,
  `notes` mediumtext DEFAULT NULL,
  `construct_id` smallint(5) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `mutation_to_fish_variant` (`variant_id`),
  KEY `mutation_to_endogenous_gene` (`gene_id`),
  KEY `mutation_to_user` (`user_id`),
  KEY `construct_to_event` (`construct_id`),
  CONSTRAINT `construct_to_event` FOREIGN KEY (`construct_id`) REFERENCES `genetic_constructs` (`id`),
  CONSTRAINT `mutation_to_endogenous_gene` FOREIGN KEY (`gene_id`) REFERENCES `genes` (`id`),
  CONSTRAINT `mutation_to_fish_variant` FOREIGN KEY (`variant_id`) REFERENCES `genetic_variants` (`id`) ON DELETE SET NULL,
  CONSTRAINT `mutation_to_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genetic_knockins`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genetic_knockins` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `gene_id` mediumint(8) unsigned NOT NULL,
  `event_id` smallint(5) unsigned NOT NULL,
  `construct_id` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gene_mutation_unique` (`gene_id`,`event_id`),
  KEY `genes_in_mutations_to_mutation` (`event_id`),
  KEY `knockin_to_construct` (`construct_id`),
  CONSTRAINT `genes_in_mutations_to_gene` FOREIGN KEY (`gene_id`) REFERENCES `genes` (`id`),
  CONSTRAINT `genes_in_mutations_to_mutation` FOREIGN KEY (`event_id`) REFERENCES `genetic_events` (`id`) ON DELETE CASCADE,
  CONSTRAINT `knockin_to_construct` FOREIGN KEY (`construct_id`) REFERENCES `genetic_constructs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `genetic_variants`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `genetic_variants` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(250) NOT NULL,
  `mother_id` mediumint(8) unsigned DEFAULT NULL,
  `father_id` mediumint(8) unsigned DEFAULT NULL,
  `lineage_type` enum('injection','cross','selection','wild-type') DEFAULT NULL,
  `date_created` date DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `fully_annotated` tinyint(1) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `mother_fish_variant_id` (`mother_id`),
  KEY `father_fish_variant_id` (`father_id`),
  KEY `creator_id` (`creator_id`),
  KEY `lineage_type` (`lineage_type`),
  CONSTRAINT `fish_variant_to_father` FOREIGN KEY (`father_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `fish_variant_to_mother` FOREIGN KEY (`mother_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `fish_variant_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locations` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(250) NOT NULL DEFAULT '',
  `purpose` varchar(250) NOT NULL DEFAULT '',
  `part_of` smallint(5) unsigned DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT 1,
  `temporary` tinyint(1) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `location_to_location` (`part_of`),
  CONSTRAINT `location_to_location` FOREIGN KEY (`part_of`) REFERENCES `locations` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `log_files`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `log_files` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `text` mediumtext NOT NULL,
  `text_sha1` binary(20) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `text_sha1` (`text_sha1`),
  KEY `log_file_to_run` (`run_id`),
  CONSTRAINT `log_file_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mandos_expression`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mandos_expression` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `gene_id` mediumint(8) unsigned NOT NULL,
  `tissue_id` smallint(5) unsigned NOT NULL,
  `developmental_stage` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `level` double NOT NULL,
  `confidence` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `external_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `gene_tissue_stage_ref_unique` (`gene_id`,`tissue_id`,`developmental_stage`,`ref_id`),
  UNIQUE KEY `external_id_ref_unique` (`external_id`,`ref_id`),
  KEY `expression_to_ref` (`ref_id`),
  KEY `expression_to_tissue` (`tissue_id`),
  KEY `confidence` (`confidence`),
  CONSTRAINT `expression_to_gene` FOREIGN KEY (`gene_id`) REFERENCES `genes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `expression_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `expression_to_tissue` FOREIGN KEY (`tissue_id`) REFERENCES `tissues` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mandos_info`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mandos_info` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `compound_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(1000) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `mandos_chem_info_name_source_compound_unique` (`name`,`ref_id`,`compound_id`),
  KEY `mandos_chem_info_to_data_source` (`ref_id`),
  KEY `name` (`name`),
  KEY `value` (`value`),
  KEY `mandos_info_to_compound` (`compound_id`),
  CONSTRAINT `mandos_chem_info_to_data_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `mandos_info_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mandos_object_links`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mandos_object_links` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `parent_id` mediumint(8) unsigned NOT NULL,
  `child_id` mediumint(8) unsigned NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  KEY `child_id` (`child_id`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `mandos_object_links_ibfk_1` FOREIGN KEY (`child_id`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_object_links_ibfk_2` FOREIGN KEY (`parent_id`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_object_links_ibfk_3` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mandos_object_tags`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mandos_object_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `object` mediumint(8) unsigned NOT NULL,
  `ref` smallint(5) unsigned NOT NULL,
  `name` varchar(150) NOT NULL,
  `value` varchar(250) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `object_ref_name_value_unique` (`object`,`ref`,`name`,`value`),
  KEY `object` (`object`),
  KEY `ref` (`ref`),
  KEY `label` (`value`),
  CONSTRAINT `mandos_object_tag_to_object` FOREIGN KEY (`object`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_object_tag_to_ref` FOREIGN KEY (`ref`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mandos_objects`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mandos_objects` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ref_id` smallint(5) unsigned NOT NULL,
  `external_id` varchar(250) NOT NULL,
  `name` varchar(250) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `data_source_external_id_unique` (`ref_id`,`external_id`),
  KEY `data_source_id` (`ref_id`),
  KEY `external_id` (`external_id`),
  CONSTRAINT `mandos_key_to_data_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mandos_predicates`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mandos_predicates` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `ref_id` smallint(5) unsigned NOT NULL,
  `external_id` varchar(250) DEFAULT NULL,
  `name` varchar(250) NOT NULL,
  `kind` enum('target','class','indication','other') NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_source_unique` (`name`,`ref_id`),
  UNIQUE KEY `external_id_source_unique` (`external_id`,`ref_id`),
  KEY `mandos_mode_to_source` (`ref_id`),
  KEY `name` (`name`),
  KEY `external_id` (`external_id`),
  CONSTRAINT `mandos_mode_to_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mandos_rule_tags`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mandos_rule_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `rule` int(10) unsigned NOT NULL,
  `ref` smallint(5) unsigned NOT NULL,
  `name` varchar(150) NOT NULL,
  `value` varchar(250) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `rule_ref_name_value_unique` (`rule`,`ref`,`name`,`value`),
  KEY `rule` (`rule`),
  KEY `label` (`value`),
  KEY `ref` (`ref`),
  CONSTRAINT `mandos_rule_tag_to_object` FOREIGN KEY (`rule`) REFERENCES `mandos_rules` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_rule_tag_to_ref` FOREIGN KEY (`ref`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mandos_rules`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mandos_rules` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ref_id` smallint(5) unsigned NOT NULL,
  `compound_id` mediumint(8) unsigned NOT NULL,
  `object_id` mediumint(8) unsigned NOT NULL,
  `external_id` varchar(250) DEFAULT NULL,
  `predicate_id` tinyint(3) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `data_source_compound_mode_unique` (`ref_id`,`compound_id`,`object_id`,`predicate_id`),
  KEY `data_source_id` (`ref_id`),
  KEY `compound_id` (`compound_id`),
  KEY `external_id` (`external_id`),
  KEY `key_id` (`object_id`),
  KEY `mode_id` (`predicate_id`),
  CONSTRAINT `mandos_association_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_association_to_data_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_association_to_key` FOREIGN KEY (`object_id`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_association_to_mode` FOREIGN KEY (`predicate_id`) REFERENCES `mandos_predicates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `plate_types`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `plate_types` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `supplier_id` smallint(5) unsigned DEFAULT NULL,
  `part_number` varchar(100) DEFAULT NULL,
  `n_rows` smallint(5) unsigned NOT NULL,
  `n_columns` smallint(5) unsigned NOT NULL,
  `well_shape` enum('round','square','rectangular') NOT NULL,
  `opacity` enum('opaque','transparent') NOT NULL,
  PRIMARY KEY (`id`),
  KEY `n_rows` (`n_rows`,`n_columns`),
  KEY `manufacturer` (`part_number`),
  KEY `plate_type_to_supplier` (`supplier_id`),
  CONSTRAINT `plate_type_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `plates`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `plates` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `plate_type_id` tinyint(3) unsigned DEFAULT NULL,
  `person_plated_id` smallint(5) unsigned NOT NULL,
  `datetime_plated` datetime DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `datetime_fish_plated` (`datetime_plated`),
  KEY `plate_to_plate_type` (`plate_type_id`),
  KEY `plate_to_user` (`person_plated_id`),
  CONSTRAINT `plate_to_plate_type` FOREIGN KEY (`plate_type_id`) REFERENCES `plate_types` (`id`),
  CONSTRAINT `plate_to_user` FOREIGN KEY (`person_plated_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_tags`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `project_id` smallint(5) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(255) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `project_tag_unique` (`project_id`,`name`),
  KEY `project_tag_to_ref` (`ref_id`),
  CONSTRAINT `project_tag_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `tag_to_project` FOREIGN KEY (`project_id`) REFERENCES `superprojects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_types`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_types` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` text NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `refs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `refs` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `datetime_downloaded` datetime DEFAULT NULL,
  `external_version` varchar(50) DEFAULT NULL,
  `description` varchar(250) DEFAULT NULL,
  `url` varchar(100) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `url` (`url`),
  KEY `name` (`name`),
  KEY `external_version` (`external_version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rois`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rois` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `well_id` mediumint(8) unsigned NOT NULL,
  `y0` smallint(6) NOT NULL,
  `x0` smallint(6) NOT NULL,
  `y1` smallint(6) NOT NULL,
  `x1` smallint(6) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `well_id` (`well_id`),
  KEY `lorien_config` (`ref_id`),
  CONSTRAINT `roi_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `roi_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `run_tags`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `run_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(10000) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `plate_run_name_unique` (`run_id`,`name`),
  CONSTRAINT `run_tag_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `runs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `runs` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `experiment_id` smallint(5) unsigned NOT NULL,
  `plate_id` smallint(5) unsigned NOT NULL,
  `description` varchar(200) NOT NULL,
  `experimentalist_id` smallint(5) unsigned NOT NULL,
  `submission_id` mediumint(8) unsigned DEFAULT NULL,
  `datetime_run` datetime NOT NULL,
  `datetime_dosed` datetime DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `tag` varchar(100) NOT NULL DEFAULT '',
  `sauron_config_id` smallint(5) unsigned NOT NULL,
  `config_file_id` smallint(5) unsigned DEFAULT NULL,
  `incubation_min` mediumint(9) DEFAULT NULL,
  `acclimation_sec` int(10) unsigned DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag_unique` (`tag`),
  UNIQUE KEY `submission_unique` (`submission_id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `datetime_dosed` (`datetime_dosed`),
  KEY `datetime_run` (`datetime_run`),
  KEY `projectalist_id` (`experimentalist_id`),
  KEY `plate_id` (`plate_id`),
  KEY `plate_run_to_sauronx_submission` (`submission_id`),
  KEY `plate_run_to_sauronx_toml` (`config_file_id`),
  KEY `sauronx_submission_id` (`submission_id`),
  KEY `legacy_name` (`name`),
  KEY `dark_adaptation_seconds` (`acclimation_sec`),
  KEY `legacy_incubation_minutes` (`incubation_min`),
  KEY `sauronx_toml_id` (`config_file_id`),
  KEY `sauron_config_id` (`sauron_config_id`),
  KEY `plate_run_to_project` (`experiment_id`),
  CONSTRAINT `plate_run_to_plate` FOREIGN KEY (`plate_id`) REFERENCES `plates` (`id`) ON DELETE CASCADE,
  CONSTRAINT `plate_run_to_project` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`),
  CONSTRAINT `plate_run_to_sauron_config` FOREIGN KEY (`sauron_config_id`) REFERENCES `sauron_configs` (`id`),
  CONSTRAINT `plate_run_to_sauronx_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`),
  CONSTRAINT `plate_run_to_sauronx_toml` FOREIGN KEY (`config_file_id`) REFERENCES `config_files` (`id`),
  CONSTRAINT `plate_run_to_user` FOREIGN KEY (`experimentalist_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sauron_configs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sauron_configs` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `sauron_id` tinyint(3) unsigned NOT NULL,
  `datetime_changed` datetime NOT NULL,
  `description` text NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauron_datetime_changed_unique` (`sauron_id`,`datetime_changed`),
  KEY `sauron_id` (`sauron_id`),
  CONSTRAINT `sauron_config_to_sauron` FOREIGN KEY (`sauron_id`) REFERENCES `saurons` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sauron_settings`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sauron_settings` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `sauron_config_id` smallint(5) unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauron_name_unique` (`sauron_config_id`,`name`),
  KEY `sauron_setting_name` (`name`),
  KEY `sauron` (`sauron_config_id`),
  CONSTRAINT `sauron_setting_to_sauron_config` FOREIGN KEY (`sauron_config_id`) REFERENCES `sauron_configs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `saurons`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `saurons` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `active` tinyint(1) unsigned NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `number` (`name`),
  KEY `current` (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sensor_data`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sensor_data` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `sensor_id` tinyint(3) unsigned NOT NULL,
  `floats` longblob NOT NULL,
  `floats_sha1` binary(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `plate_run_id` (`run_id`),
  KEY `sensor_id` (`sensor_id`),
  KEY `floats_sha1` (`floats_sha1`),
  CONSTRAINT `sensor_data_to_plate_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `sensor_data_to_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sensors`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sensors` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `data_type` enum('byte','short','int','float','double','unsigned_byte','unsigned_short','unsigned_int','unsigned_float','unsigned_double','utf8_char','long','unsigned_long','other') NOT NULL,
  `blob_type` enum('assay_start','protocol_start','every_n_milliseconds','every_n_frames','arbitrary') DEFAULT NULL,
  `n_between` int(10) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stimuli`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stimuli` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `default_color` char(6) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `analog` tinyint(1) NOT NULL DEFAULT 0,
  `rgb` binary(3) DEFAULT NULL,
  `wavelength_nm` smallint(5) unsigned DEFAULT NULL,
  `audio_file_id` smallint(5) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  UNIQUE KEY `audio_file_id_unique` (`audio_file_id`),
  CONSTRAINT `stimulus_to_audio_file` FOREIGN KEY (`audio_file_id`) REFERENCES `audio_files` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stimulus_frames`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stimulus_frames` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `assay_id` smallint(5) unsigned NOT NULL,
  `stimulus_id` smallint(5) unsigned NOT NULL,
  `frames` longblob NOT NULL,
  `frames_sha1` binary(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assay_id_stimulus_id` (`assay_id`,`stimulus_id`),
  KEY `assay_id` (`assay_id`),
  KEY `stimulus_id` (`stimulus_id`),
  KEY `frames_sha1` (`frames_sha1`),
  CONSTRAINT `stimulus_frames_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stimulus_frames_to_stimulus` FOREIGN KEY (`stimulus_id`) REFERENCES `stimuli` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submission_params`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submission_params` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `submission_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(250) NOT NULL,
  `param_type` enum('n_fish','compound','dose','variant','dpf','group') NOT NULL,
  `value` varchar(4000) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauronx_submission_name_unique` (`submission_id`,`name`),
  CONSTRAINT `sauronx_submission_parameter_to_sauronx_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submission_records`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submission_records` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `submission_id` mediumint(8) unsigned NOT NULL,
  `status` enum('starting','capturing','failed','cancelled','extracting','extracted','compressing','compressed','uploading','uploaded','inserting','inserted run','inserting features','inserted features','inserting sensors','inserted sensors','insert failed','archiving','archived','available','failed_during_initialization','failed_during_capture','failed_during_postprocessing','failed_during_upload','cancelled_during_capture','finished_capture') DEFAULT NULL,
  `sauron_id` tinyint(3) unsigned NOT NULL,
  `datetime_modified` datetime NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `sauronx_submission_history_to_sauron` (`sauron_id`),
  KEY `sauronx_submission_history_to_submission` (`submission_id`),
  CONSTRAINT `sauronx_submission_history_to_sauron` FOREIGN KEY (`sauron_id`) REFERENCES `saurons` (`id`),
  CONSTRAINT `sauronx_submission_history_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submissions`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `submissions` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `lookup_hash` char(12) NOT NULL,
  `experiment_id` smallint(5) unsigned NOT NULL,
  `user_id` smallint(5) unsigned NOT NULL,
  `person_plated_id` smallint(5) unsigned NOT NULL,
  `continuing_id` mediumint(8) unsigned DEFAULT NULL,
  `datetime_plated` datetime NOT NULL,
  `datetime_dosed` datetime DEFAULT NULL,
  `acclimation_sec` int(10) unsigned DEFAULT NULL,
  `description` varchar(250) NOT NULL,
  `notes` mediumtext DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_hash_hex` (`lookup_hash`),
  KEY `sauronx_submission_to_project` (`experiment_id`),
  KEY `sauronx_submission_to_user` (`user_id`),
  KEY `sauronx_submission_to_plate` (`continuing_id`),
  KEY `sauronx_submission_to_person_plated` (`person_plated_id`),
  CONSTRAINT `matched_submission` FOREIGN KEY (`continuing_id`) REFERENCES `submissions` (`id`),
  CONSTRAINT `sauronx_submission_to_person_plated` FOREIGN KEY (`person_plated_id`) REFERENCES `users` (`id`),
  CONSTRAINT `sauronx_submission_to_project` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`),
  CONSTRAINT `sauronx_submission_to_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `superprojects`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `superprojects` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `type_id` tinyint(3) unsigned DEFAULT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `reason` mediumtext DEFAULT NULL,
  `methods` mediumtext DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT 1,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `primary_author_id` (`creator_id`),
  KEY `project_to_project_type` (`type_id`),
  CONSTRAINT `project_to_project_type` FOREIGN KEY (`type_id`) REFERENCES `project_types` (`id`),
  CONSTRAINT `superproject_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `suppliers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `suppliers` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `created` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template_assays`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template_assays` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `author_id` smallint(5) unsigned DEFAULT NULL,
  `specializes` smallint(5) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `author_index` (`author_id`),
  KEY `template_protocol_specialization` (`specializes`),
  CONSTRAINT `template_assay_specialization` FOREIGN KEY (`specializes`) REFERENCES `template_assays` (`id`) ON DELETE SET NULL,
  CONSTRAINT `template_assay_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template_plates`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template_plates` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(10000) DEFAULT NULL,
  `plate_type_id` tinyint(3) unsigned NOT NULL,
  `author_id` smallint(5) unsigned NOT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  `specializes` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `author_index` (`author_id`),
  KEY `template_plate_specialization` (`specializes`),
  KEY `template_plate_to_plate_type` (`plate_type_id`),
  CONSTRAINT `template_plate_specialization` FOREIGN KEY (`specializes`) REFERENCES `template_plates` (`id`) ON DELETE SET NULL,
  CONSTRAINT `template_plate_to_plate_type` FOREIGN KEY (`plate_type_id`) REFERENCES `plate_types` (`id`),
  CONSTRAINT `template_plate_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template_stimulus_frames`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template_stimulus_frames` (
  `id` mediumint(6) unsigned NOT NULL AUTO_INCREMENT,
  `template_assay_id` smallint(5) unsigned NOT NULL,
  `range_expression` varchar(150) NOT NULL,
  `stimulus_id` smallint(5) unsigned NOT NULL,
  `value_expression` varchar(250) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `stimulus_index` (`stimulus_id`),
  KEY `template_protocol` (`template_assay_id`),
  CONSTRAINT `template_frames_to_template_assay` FOREIGN KEY (`template_assay_id`) REFERENCES `template_assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `template_stimulus_frames_to_stimulus` FOREIGN KEY (`stimulus_id`) REFERENCES `stimuli` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template_treatments`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template_treatments` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `template_plate_id` smallint(5) unsigned NOT NULL,
  `well_range_expression` varchar(100) NOT NULL,
  `batch_expression` varchar(250) NOT NULL,
  `dose_expression` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `template_plate_id` (`template_plate_id`),
  CONSTRAINT `template_well_to_template_plate` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template_wells`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template_wells` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `template_plate_id` smallint(5) unsigned NOT NULL,
  `well_range_expression` varchar(255) NOT NULL,
  `control_type` tinyint(3) unsigned DEFAULT NULL,
  `n_expression` varchar(250) NOT NULL,
  `variant_expression` varchar(250) NOT NULL,
  `age_expression` varchar(255) NOT NULL,
  `group_expression` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tw_to_tp` (`template_plate_id`),
  KEY `template_well_to_control_type` (`control_type`),
  CONSTRAINT `template_well_to_control_type` FOREIGN KEY (`control_type`) REFERENCES `control_types` (`id`),
  CONSTRAINT `tw_to_tp` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tissues`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tissues` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `external_id` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id_ref_unique` (`external_id`,`ref_id`),
  KEY `tissue_to_ref` (`ref_id`),
  KEY `name` (`name`),
  CONSTRAINT `tissue_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transfer_plates`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transfer_plates` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(250) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `plate_type_id` tinyint(3) unsigned NOT NULL,
  `supplier_id` smallint(5) unsigned DEFAULT NULL,
  `parent_id` smallint(5) unsigned DEFAULT NULL,
  `dilution_factor_from_parent` double unsigned DEFAULT NULL,
  `initial_ul_per_well` double unsigned NOT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `datetime_created` datetime NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `transfer_plate_to_plate_type` (`plate_type_id`),
  KEY `transfer_plate_to_creator` (`creator_id`),
  KEY `transfer_plate_to_parent` (`parent_id`),
  KEY `transfer_plate_to_supplier` (`supplier_id`),
  CONSTRAINT `transfer_plate_to_creator` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `transfer_plate_to_parent` FOREIGN KEY (`parent_id`) REFERENCES `transfer_plates` (`id`),
  CONSTRAINT `transfer_plate_to_plate_type` FOREIGN KEY (`plate_type_id`) REFERENCES `plate_types` (`id`),
  CONSTRAINT `transfer_plate_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `write_access` tinyint(1) NOT NULL DEFAULT 1,
  `bcrypt_hash` char(60) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_unique` (`username`),
  KEY `bcrypt_hash` (`bcrypt_hash`),
  KEY `first_name` (`first_name`),
  KEY `last_name` (`last_name`),
  KEY `write_access` (`write_access`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `well_features`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `well_features` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `well_id` mediumint(8) unsigned NOT NULL,
  `type_id` tinyint(3) unsigned NOT NULL,
  `floats` longblob NOT NULL,
  `sha1` binary(40) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `type_id` (`type_id`),
  KEY `sha1` (`sha1`),
  KEY `well_id` (`well_id`),
  CONSTRAINT `well_feature_to_type` FOREIGN KEY (`type_id`) REFERENCES `features` (`id`),
  CONSTRAINT `well_feature_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `well_treatments`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `well_treatments` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `well_id` mediumint(8) unsigned NOT NULL,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `micromolar_dose` double unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `well_id` (`well_id`,`batch_id`),
  KEY `compound_id` (`batch_id`),
  KEY `well_id_2` (`well_id`),
  CONSTRAINT `well_treatment_to_ordered_compound` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`),
  CONSTRAINT `well_treatment_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wells`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wells` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `well_index` smallint(5) unsigned NOT NULL,
  `control_type_id` tinyint(3) unsigned DEFAULT NULL,
  `variant_id` mediumint(8) unsigned DEFAULT NULL,
  `well_group` varchar(50) DEFAULT NULL,
  `n` mediumint(9) NOT NULL DEFAULT 0,
  `age` mediumint(8) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `plate_well_index_unique` (`run_id`,`well_index`),
  KEY `plate_id` (`run_id`),
  KEY `fish_variant_id` (`variant_id`),
  KEY `well_group` (`well_group`),
  KEY `well_to_control_type` (`control_type_id`),
  KEY `approx_n_fish` (`n`),
  KEY `well_index` (`well_index`),
  CONSTRAINT `well_to_control_type` FOREIGN KEY (`control_type_id`) REFERENCES `control_types` (`id`),
  CONSTRAINT `well_to_fish_variant` FOREIGN KEY (`variant_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `well_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
