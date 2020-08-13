/*
Sample Insertion SQL Queries to populate test db. Make sure unique keys are different for the VALUES.
*/


-- Host: 127.0.0.1    Database: valartest
-- ------------------------------------------------------

SET FOREIGN_KEY_CHECKS=0;

DROP DATABASE IF EXISTS valartest;
CREATE DATABASE valartest CHARACTER SET = 'utf8mb4' COLLATE 'utf8mb4_unicode_520_ci';
DROP USER IF EXISTS 'chemfishtest'@'localhost';
USE valartest;
CREATE USER 'chemfishtest'@'localhost' IDENTIFIED BY 'chemfish123';
GRANT SELECT, INSERT, UPDATE, DELETE ON valartest.* TO 'chemfishtest'@'localhost';


--
-- Table structure for table `annotations`
--

CREATE TABLE `annotations` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `value` varchar(255) DEFAULT NULL,
  `level` enum('0:good', '1:note', '2:caution', '3:warning', '4:danger', '9:deleted', 'to_fix', 'fixed') NOT NULL DEFAULT '1:note',
  `run_id` mediumint(8) unsigned DEFAULT NULL,
  `submission_id` mediumint(8) unsigned DEFAULT NULL,
  `well_id` mediumint(8) unsigned DEFAULT NULL,
  `assay_id` smallint(5) unsigned DEFAULT NULL,
  `annotator_id` smallint(5) unsigned NOT NULL,
  `description` mediumtext DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `annotation_to_run` (`run_id`),
  KEY `annotation_to_well` (`well_id`),
  KEY `annotation_to_assay` (`assay_id`),
  KEY `annotation_to_person` (`annotator_id`),
  KEY `level` (`level`),
  KEY `name` (`name`),
  KEY `annotation_to_submission` (`submission_id`),
  KEY `value` (`value`),
  CONSTRAINT `annotation_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_person` FOREIGN KEY (`annotator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `annotation_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `annotation_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `api_keys`
--

CREATE TABLE `api_keys` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `value` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `assay_params`
--

CREATE TABLE `assay_params` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `assay_id` smallint(5) unsigned NOT NULL,
  `name` varchar(30) CHARACTER SET latin1 NOT NULL,
  `value` double NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assay_and_name_unique` (`name`, `assay_id`),
  KEY `assay_param_to_assay` (`assay_id`),
  KEY `value` (`value`),
  CONSTRAINT `assay_param_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `assay_positions`
--

CREATE TABLE `assay_positions` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `battery_id` smallint(5) unsigned NOT NULL,
  `assay_id` smallint(5) unsigned NOT NULL,
  `start` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `battery_assay_start_unique` (`battery_id`, `assay_id`, `start`),
  KEY `battery_id` (`battery_id`),
  KEY `assay_id` (`assay_id`),
  KEY `start` (`start`),
  CONSTRAINT `assay_in_battery_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`),
  CONSTRAINT `assay_in_battery_to_battery` FOREIGN KEY (`battery_id`) REFERENCES `batteries` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `assays`
--

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
  UNIQUE KEY `name_frames_sha1_unique` (`name`, `frames_sha1`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `name` (`name`),
  KEY `hash` (`frames_sha1`) USING BTREE,
  KEY `assay_to_template_assay` (`template_assay_id`),
  CONSTRAINT `assay_to_template_assay` FOREIGN KEY (`template_assay_id`) REFERENCES `template_assays` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `audio_files`
--

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


--
-- Table structure for table `batch_annotations`
--

CREATE TABLE `batch_annotations` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `level` enum('0:good', '1:note', '2:caution', '3:warning', '4:danger', '9:deleted') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '1:note',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `value` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `annotator_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `batch_annotation_to_batch` (`batch_id`),
  KEY `batch_annotation_to_user` (`annotator_id`),
  KEY `level` (`level`),
  KEY `name` (`name`),
  KEY `value` (`value`),
  CONSTRAINT `batch_annotation_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE CASCADE,
  CONSTRAINT `batch_annotation_to_user` FOREIGN KEY (`annotator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `batch_labels`
--

CREATE TABLE `batch_labels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `name` varchar(250) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `batch_name` (`name`),
  KEY `batch_ref` (`ref_id`),
  KEY `batch_id` (`batch_id`),
  CONSTRAINT `batch_id_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`) ON DELETE CASCADE,
  CONSTRAINT `batch_label_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `batches`
--

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
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_hash` (`lookup_hash`),
  UNIQUE KEY `box_number_well_number` (`box_number`, `well_number`),
  UNIQUE KEY `tag_unique` (`tag`),
  KEY `compound_id` (`compound_id`),
  KEY `solvent_id` (`solvent_id`),
  KEY `internal_id` (`legacy_internal_id`) USING BTREE,
  KEY `batch_to_ref` (`ref_id`),
  KEY `batch_to_user` (`person_ordered`),
  KEY `batch_to_supplier` (`supplier_id`),
  KEY `date_ordered` (`date_ordered`),
  KEY `box_number` (`box_number`),
  KEY `well_number` (`well_number`),
  KEY `batch_to_batch` (`made_from_id`),
  KEY `batch_to_location` (`location_id`),
  CONSTRAINT `batch_to_batch` FOREIGN KEY (`made_from_id`) REFERENCES `batches` (`id`),
  CONSTRAINT `batch_to_location` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`),
  CONSTRAINT `batch_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
  CONSTRAINT `batch_to_external_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `batch_to_solvent` FOREIGN KEY (`solvent_id`) REFERENCES `compounds` (`id`),
  CONSTRAINT `batch_to_user` FOREIGN KEY (`person_ordered`) REFERENCES `users` (`id`),
  CONSTRAINT `batch_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `batteries`
--

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
  KEY `battery_to_template` (`template_id`),
  KEY `length` (`length`),
  KEY `assays_sha1` (`assays_sha1`),
  CONSTRAINT `battery_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `compound_labels`
--

CREATE TABLE `compound_labels` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `compound_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(1000) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `compound_id` (`compound_id`),
  KEY `compound_name_to_ref` (`ref_id`),
  CONSTRAINT `compound_name_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE,
  CONSTRAINT `compound_name_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `compounds`
--

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


--
-- Table structure for table `config_files`
--

CREATE TABLE `config_files` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `toml_text` mediumtext NOT NULL,
  `text_sha1` binary(20) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `text_sha1_unique` (`text_sha1`),
  KEY `text_sha1` (`text_sha1`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `control_types`
--

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


--
-- Table structure for table `experiment_tags`
--

CREATE TABLE `experiment_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `experiment_id` smallint(5) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(255) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `exp_tag_unique` (`experiment_id`, `name`),
  KEY `experiment_tag_to_ref` (`ref_id`),
  CONSTRAINT `experiment_tag_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `tag_to_experiment` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `experiments`
--

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
  KEY `battery_id` (`battery_id`),
  KEY `project_to_superproject` (`project_id`),
  KEY `project_to_template_plate` (`template_plate_id`),
  KEY `experiment_to_transfer_plate` (`transfer_plate_id`),
  KEY `experiment_to_user` (`creator_id`),
  CONSTRAINT `experiment_to_transfer_plate` FOREIGN KEY (`transfer_plate_id`) REFERENCES `transfer_plates` (`id`),
  CONSTRAINT `experiment_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`),
  CONSTRAINT `project_to_battery` FOREIGN KEY (`battery_id`) REFERENCES `batteries` (`id`),
  CONSTRAINT `project_to_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `project_to_template_plate` FOREIGN KEY (`template_plate_id`) REFERENCES `template_plates` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `features`
--

CREATE TABLE `features` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) NOT NULL,
  `dimensions` varchar(20) NOT NULL,
  `data_type` enum('byte', 'short', 'int', 'float', 'double', 'unsigned_byte', 'unsigned_short', 'unsigned_int', 'unsigned_float', 'unsigned_double', 'utf8_char') NOT NULL DEFAULT 'float',
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `genetic_variants`
--

CREATE TABLE `genetic_variants` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(250) NOT NULL,
  `mother_id` mediumint(8) unsigned DEFAULT NULL,
  `father_id` mediumint(8) unsigned DEFAULT NULL,
  `lineage_type` enum('injection', 'cross', 'selection', 'wild-type') DEFAULT NULL,
  `date_created` date DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `creator_id` smallint(5) unsigned NOT NULL,
  `fully_annotated` tinyint(1) NOT NULL DEFAULT 0,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`),
  KEY `mother_variant_id` (`mother_id`),
  KEY `father_variant_id` (`father_id`),
  KEY `creator_id` (`creator_id`),
  KEY `lineage_type` (`lineage_type`),
  CONSTRAINT `variant_to_father` FOREIGN KEY (`father_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `variant_to_mother` FOREIGN KEY (`mother_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `variant_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `locations`
--

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


--
-- Table structure for table `log_files`
--

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


--
-- Table structure for table `mandos_info`
--

CREATE TABLE `mandos_info` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `compound_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(1000) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `mandos_chem_info_name_source_compound_unique` (`name`, `ref_id`, `compound_id`),
  KEY `mandos_chem_info_to_data_source` (`ref_id`),
  KEY `name` (`name`),
  KEY `value` (`value`),
  KEY `mandos_info_to_compound` (`compound_id`),
  CONSTRAINT `mandos_chem_info_to_data_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `mandos_info_to_compound` FOREIGN KEY (`compound_id`) REFERENCES `compounds` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_object_links`
--

CREATE TABLE `mandos_object_links` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `parent_id` mediumint(8) unsigned NOT NULL,
  `child_id` mediumint(8) unsigned NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  KEY `child_id` (`child_id`),
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `mandos_object_link_to_child` FOREIGN KEY (`child_id`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_object_link_to_parent` FOREIGN KEY (`parent_id`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_object_link_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `mandos_object_tags`
--

CREATE TABLE `mandos_object_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `object` mediumint(8) unsigned NOT NULL,
  `ref` smallint(5) unsigned NOT NULL,
  `name` varchar(150) NOT NULL,
  `value` varchar(250) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `object_ref_name_value_unique` (`object`, `ref`, `name`, `value`),
  KEY `object` (`object`),
  KEY `ref` (`ref`),
  KEY `label` (`value`),
  CONSTRAINT `mandos_object_tag_to_object` FOREIGN KEY (`object`) REFERENCES `mandos_objects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_object_tag_to_ref` FOREIGN KEY (`ref`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_objects`
--

CREATE TABLE `mandos_objects` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ref_id` smallint(5) unsigned NOT NULL,
  `external_id` varchar(250) NOT NULL,
  `name` varchar(250) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `data_source_external_id_unique` (`ref_id`, `external_id`),
  KEY `data_source_id` (`ref_id`),
  KEY `external_id` (`external_id`),
  CONSTRAINT `mandos_key_to_data_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_predicates`
--

CREATE TABLE `mandos_predicates` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `ref_id` smallint(5) unsigned NOT NULL,
  `external_id` varchar(250) DEFAULT NULL,
  `name` varchar(250) NOT NULL,
  `kind` enum('target', 'class', 'indication', 'other') NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_source_unique` (`name`, `ref_id`),
  UNIQUE KEY `external_id_source_unique` (`external_id`, `ref_id`),
  KEY `mandos_mode_to_source` (`ref_id`),
  KEY `name` (`name`),
  KEY `external_id` (`external_id`),
  CONSTRAINT `mandos_mode_to_source` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_rule_tags`
--

CREATE TABLE `mandos_rule_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `rule` int(10) unsigned NOT NULL,
  `ref` smallint(5) unsigned NOT NULL,
  `name` varchar(150) NOT NULL,
  `value` varchar(250) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `rule_ref_name_value_unique` (`rule`, `ref`, `name`, `value`),
  KEY `rule` (`rule`),
  KEY `label` (`value`),
  KEY `ref` (`ref`),
  CONSTRAINT `mandos_rule_tag_to_object` FOREIGN KEY (`rule`) REFERENCES `mandos_rules` (`id`) ON DELETE CASCADE,
  CONSTRAINT `mandos_rule_tag_to_ref` FOREIGN KEY (`ref`) REFERENCES `refs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `mandos_rules`
--

CREATE TABLE `mandos_rules` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ref_id` smallint(5) unsigned NOT NULL,
  `compound_id` mediumint(8) unsigned NOT NULL,
  `object_id` mediumint(8) unsigned NOT NULL,
  `external_id` varchar(250) DEFAULT NULL,
  `predicate_id` tinyint(3) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `data_source_compound_mode_unique` (`ref_id`, `compound_id`, `object_id`, `predicate_id`),
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


--
-- Table structure for table `plate_types`
--

CREATE TABLE `plate_types` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `supplier_id` smallint(5) unsigned DEFAULT NULL,
  `part_number` varchar(100) DEFAULT NULL,
  `n_rows` smallint(5) unsigned NOT NULL,
  `n_columns` smallint(5) unsigned NOT NULL,
  `well_shape` enum('round', 'square', 'rectangular') NOT NULL,
  `opacity` enum('opaque', 'transparent') NOT NULL,
  PRIMARY KEY (`id`),
  KEY `n_rows` (`n_rows`, `n_columns`),
  KEY `manufacturer` (`part_number`),
  KEY `plate_type_to_supplier` (`supplier_id`),
  CONSTRAINT `plate_type_to_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `plates`
--

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


--
-- Table structure for table `project_tags`
--

CREATE TABLE `project_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `project_id` smallint(5) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(255) NOT NULL,
  `ref_id` smallint(5) unsigned NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `project_tag_unique` (`project_id`, `name`),
  KEY `project_tag_to_ref` (`ref_id`),
  CONSTRAINT `project_tag_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `tag_to_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `project_types`
--

CREATE TABLE `project_types` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` text NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_unique` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `refs`
--

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


--
-- Table structure for table `rois`
--

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
  KEY `ref_id` (`ref_id`),
  CONSTRAINT `roi_to_ref` FOREIGN KEY (`ref_id`) REFERENCES `refs` (`id`),
  CONSTRAINT `roi_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `run_tags`
--

CREATE TABLE `run_tags` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(10000) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `run_name_unique` (`run_id`, `name`),
  CONSTRAINT `run_tag_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `runs`
--

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
  KEY `run_to_submission` (`submission_id`),
  KEY `run_to_sauronx_toml` (`config_file_id`),
  KEY `submission_id` (`submission_id`),
  KEY `legacy_name` (`name`),
  KEY `dark_adaptation_seconds` (`acclimation_sec`),
  KEY `legacy_incubation_minutes` (`incubation_min`),
  KEY `sauronx_toml_id` (`config_file_id`),
  KEY `sauron_config_id` (`sauron_config_id`),
  KEY `run_to_project` (`experiment_id`),
  CONSTRAINT `run_to_plate` FOREIGN KEY (`plate_id`) REFERENCES `plates` (`id`) ON DELETE CASCADE,
  CONSTRAINT `run_to_project` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`),
  CONSTRAINT `run_to_sauron_config` FOREIGN KEY (`sauron_config_id`) REFERENCES `sauron_configs` (`id`),
  CONSTRAINT `run_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`),
  CONSTRAINT `run_to_sauronx_toml` FOREIGN KEY (`config_file_id`) REFERENCES `config_files` (`id`),
  CONSTRAINT `run_to_user` FOREIGN KEY (`experimentalist_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `sauron_configs`
--

CREATE TABLE `sauron_configs` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `sauron_id` tinyint(3) unsigned NOT NULL,
  `datetime_changed` datetime NOT NULL,
  `description` text NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauron_datetime_changed_unique` (`sauron_id`, `datetime_changed`),
  KEY `sauron_id` (`sauron_id`),
  CONSTRAINT `sauron_config_to_sauron` FOREIGN KEY (`sauron_id`) REFERENCES `saurons` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `sauron_settings`
--

CREATE TABLE `sauron_settings` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `sauron_config_id` smallint(5) unsigned NOT NULL,
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `sauron_name_unique` (`sauron_config_id`, `name`),
  KEY `sauron_setting_name` (`name`),
  KEY `sauron` (`sauron_config_id`),
  CONSTRAINT `sauron_setting_to_sauron_config` FOREIGN KEY (`sauron_config_id`) REFERENCES `sauron_configs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `saurons`
--

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


--
-- Table structure for table `sensor_data`
--

CREATE TABLE `sensor_data` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` mediumint(8) unsigned NOT NULL,
  `sensor_id` tinyint(3) unsigned NOT NULL,
  `floats` longblob NOT NULL,
  `floats_sha1` binary(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`),
  KEY `sensor_id` (`sensor_id`),
  KEY `floats_sha1` (`floats_sha1`),
  CONSTRAINT `sensor_data_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `sensor_data_to_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `sensors`
--

CREATE TABLE `sensors` (
  `id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `data_type` enum('byte', 'short', 'int', 'float', 'double', 'unsigned_byte', 'unsigned_short', 'unsigned_int', 'unsigned_float', 'unsigned_double', 'utf8_char', 'long', 'unsigned_long', 'other') NOT NULL,
  `blob_type` enum('assay_start', 'battery_start', 'every_n_milliseconds', 'every_n_frames', 'arbitrary') DEFAULT NULL,
  `n_between` int(10) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `stimuli`
--

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


--
-- Table structure for table `stimulus_frames`
--

CREATE TABLE `stimulus_frames` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `assay_id` smallint(5) unsigned NOT NULL,
  `stimulus_id` smallint(5) unsigned NOT NULL,
  `frames` longblob NOT NULL,
  `frames_sha1` binary(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `assay_id_stimulus_id` (`assay_id`, `stimulus_id`),
  KEY `assay_id` (`assay_id`),
  KEY `stimulus_id` (`stimulus_id`),
  KEY `frames_sha1` (`frames_sha1`),
  CONSTRAINT `stimulus_frames_to_assay` FOREIGN KEY (`assay_id`) REFERENCES `assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stimulus_frames_to_stimulus` FOREIGN KEY (`stimulus_id`) REFERENCES `stimuli` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `submission_params`
--

CREATE TABLE `submission_params` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `submission_id` mediumint(8) unsigned NOT NULL,
  `name` varchar(250) NOT NULL,
  `param_type` enum('n_fish', 'compound', 'dose', 'variant', 'dpf', 'group') NOT NULL,
  `value` varchar(4000) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `submission_name_unique` (`submission_id`, `name`),
  CONSTRAINT `submission_parameter_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `submission_records`
--

CREATE TABLE `submission_records` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `submission_id` mediumint(8) unsigned NOT NULL,
  `status` enum('starting', 'capturing', 'failed', 'cancelled', 'extracting', 'extracted', 'compressing', 'compressed', 'uploading', 'uploaded', 'inserting', 'inserted run', 'inserting features', 'inserted features', 'inserting sensors', 'inserted sensors', 'insert failed', 'archiving', 'archived', 'available', 'failed_during_initialization', 'failed_during_capture', 'failed_during_postprocessing', 'failed_during_upload', 'cancelled_during_capture', 'finished_capture') DEFAULT NULL,
  `sauron_id` tinyint(3) unsigned NOT NULL,
  `datetime_modified` datetime NOT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `submission_history_to_sauron` (`sauron_id`),
  KEY `submission_history_to_submission` (`submission_id`),
  CONSTRAINT `submission_history_to_sauron` FOREIGN KEY (`sauron_id`) REFERENCES `saurons` (`id`),
  CONSTRAINT `submission_history_to_submission` FOREIGN KEY (`submission_id`) REFERENCES `submissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `submissions`
--

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
  KEY `submission_to_project` (`experiment_id`),
  KEY `submission_to_user` (`user_id`),
  KEY `submission_to_plate` (`continuing_id`),
  KEY `submission_to_person_plated` (`person_plated_id`),
  CONSTRAINT `matched_submission` FOREIGN KEY (`continuing_id`) REFERENCES `submissions` (`id`),
  CONSTRAINT `submission_to_person_plated` FOREIGN KEY (`person_plated_id`) REFERENCES `users` (`id`),
  CONSTRAINT `submission_to_project` FOREIGN KEY (`experiment_id`) REFERENCES `experiments` (`id`),
  CONSTRAINT `submission_to_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `projects`
--

CREATE TABLE `projects` (
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
  CONSTRAINT `project_to_user` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `suppliers`
--

CREATE TABLE `suppliers` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(250) DEFAULT NULL,
  `created` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `template_assays`
--

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
  KEY `template_battery_specialization` (`specializes`),
  CONSTRAINT `template_assay_specialization` FOREIGN KEY (`specializes`) REFERENCES `template_assays` (`id`) ON DELETE SET NULL,
  CONSTRAINT `template_assay_to_user` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `template_plates`
--

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


--
-- Table structure for table `template_stimulus_frames`
--

CREATE TABLE `template_stimulus_frames` (
  `id` mediumint(6) unsigned NOT NULL AUTO_INCREMENT,
  `template_assay_id` smallint(5) unsigned NOT NULL,
  `range_expression` varchar(150) NOT NULL,
  `stimulus_id` smallint(5) unsigned NOT NULL,
  `value_expression` varchar(250) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `stimulus_index` (`stimulus_id`),
  KEY `template_battery` (`template_assay_id`),
  CONSTRAINT `template_frames_to_template_assay` FOREIGN KEY (`template_assay_id`) REFERENCES `template_assays` (`id`) ON DELETE CASCADE,
  CONSTRAINT `template_stimulus_frames_to_stimulus` FOREIGN KEY (`stimulus_id`) REFERENCES `stimuli` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `template_treatments`
--

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


--
-- Table structure for table `template_wells`
--

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



--
-- Table structure for table `transfer_plates`
--

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


--
-- Table structure for table `users`
--

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


--
-- Table structure for table `well_features`
--

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


--
-- Table structure for table `well_treatments`
--

CREATE TABLE `well_treatments` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `well_id` mediumint(8) unsigned NOT NULL,
  `batch_id` mediumint(8) unsigned NOT NULL,
  `micromolar_dose` double unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `well_batch` (`well_id`, `batch_id`),
  KEY `compound_id` (`batch_id`),
  KEY `well_id` (`well_id`),
  CONSTRAINT `well_treatment_to_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches` (`id`),
  CONSTRAINT `well_treatment_to_well` FOREIGN KEY (`well_id`) REFERENCES `wells` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


--
-- Table structure for table `wells`
--

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
  UNIQUE KEY `plate_well_index_unique` (`run_id`, `well_index`),
  KEY `plate_id` (`run_id`),
  KEY `variant_id` (`variant_id`),
  KEY `well_group` (`well_group`),
  KEY `well_to_control_type` (`control_type_id`),
  KEY `approx_n_fish` (`n`),
  KEY `well_index` (`well_index`),
  CONSTRAINT `well_to_control_type` FOREIGN KEY (`control_type_id`) REFERENCES `control_types` (`id`),
  CONSTRAINT `well_to_variant` FOREIGN KEY (`variant_id`) REFERENCES `genetic_variants` (`id`),
  CONSTRAINT `well_to_run` FOREIGN KEY (`run_id`) REFERENCES `runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;


INSERT INTO users(
    id, username, first_name, last_name, write_access, bcrypt_hash
) VALUES (
    4, 'test_user7', 'test', 'UserBser', 0, 'jfEHa6wjtC6Fyx95F8miqtgZCSG0V35ZE82EGY3BS5kccr80Y8g3tbTWOzf7'
);

INSERT INTO submissions(
    id, lookup_hash, experiment_id, user_id, person_plated_id, continuing_id, datetime_plated, datetime_dosed,
    acclimation_sec, description, notes, created
) VALUES (
    25, '9p0MKHbf5P3m', 3, 2, 1, 1, '2019-01-26 10:11:12', '2019-01-26 11:11:12', 50, 'this is submission 25', NULL,
    now()
);

INSERT INTO runs(
    id, experiment_id, plate_id, description, experimentalist_id, submission_id, datetime_run, datetime_dosed, name,
    tag, sauron_config_id, config_file_id, incubation_min, acclimation_sec, notes
) VALUES (
    4, 2, 1, 'run number four', 1, 25, '2019-01-28 10:11:12', '2019-01-28 10:42:12', 'run_number_four', 'tag_four', 3, 1,
    20, 50, 'hi there r no notes here'
);

INSERT INTO run_tags(
    id, run_id, name, value
) VALUES(3, 1, 'second run tag', '0abcdefghijklmnop');

INSERT INTO run_tags(
    id, run_id, name, value
) VALUES(4, 1, 'sauronx_version', '54554512asofja109');

INSERT INTO submission_params(
    id, submission_id, name, param_type, value
) VALUES (
    5, 2, '$...BC123', 'compound', '\["AB0124403", "AB0124404"\]'
);

INSERT INTO submission_params(
    id, submission_id, name, param_type, value
) VALUES (
    4, 1, 'sp_1_7', 'dose', 100
);

INSERT INTO compounds(
    id, inchi, inchikey, inchikey_connectivity, chembl_id, chemspider_id, smiles
) VALUES (
    3, 'inchi_foo_bar', 'AQWEFNOQVPJJNP-UHFFFAOYSA-N', 'q42345ghijklbs', '113109-290-1', 1101145, 'C=C-B=C-H'
);

INSERT INTO locations(
    id, name, description, purpose, part_of, temporary
) VALUES(4, 'location_three', 'hello this is location three', 'purpose three', 2, 0);

INSERT INTO batches(
    id, lookup_hash, tag, compound_id, made_from_id, supplier_id, ref_id, legacy_internal_id, location_id, box_number,
    well_number, location_note, amount, concentration_millimolar, solvent_id, molecular_weight, supplier_catalog_number,
    person_ordered, date_ordered, notes
) VALUES (
    4, '124bff34abagzf', 'wrong_legacy_id_format', 1, NULL, 1, 1, 'BC000040201', 2, 5, 2, 'location three', '200ul', 100,
    2, 25.0, 1, 1, now(), 'hello this is notes_six'
);

INSERT INTO genetic_variants (
    id, name, mother_id, father_id, lineage_type, date_created, notes, creator_id, fully_annotated
) VALUES (
    4, 'genetic variant four', 7, 5, 'cross', now(), 'notes for gene four', 1, 0
);

INSERT INTO refs(
    id, name, datetime_downloaded, external_version, description, url
) VALUES (
    4, 'ref_four', '2019-01-29 12:48:12', 'ref_four_external_version', 'this is ref four',
    'https://www.nonexistentreffour.com'
);

INSERT INTO sensors(
    id, name, description, data_type, blob_type, n_between
) VALUES (
    4, 'sensor_four', 'this is sensor four.', 'long', 'assay_start', 10
);

INSERT INTO sensor_data (
    id, run_id, sensor_id, floats, floats_sha1
) VALUES (
    5, 2, 3,
    1234134093401234987234980721384712934324913448123098409185908135981039581958112379573578136793134696676741671761515747642724576,
    cast(2819 as Binary(20))
);

INSERT INTO control_types (
    id, name, description, positive, drug_related, genetics_related
) VALUES (
    3, 'control type three', 'this is control type three', 1, 1, 1
);

INSERT INTO wells(
    id, run_id, well_index, control_type_id, variant_id, well_group, n, age
) VALUES (
    9, 1, 7, 2, 5, 'well group one', 6, 15
);

INSERT INTO well_features (
    id, well_id, type_id, floats, sha1
) VALUES (
    6, 2, 2, 1929014393149134898314981349831498134981341311234143, cast(2111 as Binary(20))
);

INSERT INTO stimuli(
    id, name, default_color, description, analog, rgb, wavelength_nm, audio_file_id
) VALUES (
    3, 'none', 'ffffff', NULL, 1, NULL, NULL, NULL
);

INSERT INTO stimulus_frames (
    id, assay_id, stimulus_id, frames, frames_sha1
) VALUES (
    7, 5, 1, '78654131412341132413409876341324329048132984901238490821394081239080913859018340981349921384',
    cast(101109 as Binary(20))
);

INSERT INTO assays(
    id, name, description, length, hidden, template_assay_id, frames_sha1
) VALUES (
    5, 'assay_five', 'this is assay five', 100, 0, 2, cast(122333 as Binary(20))
);

INSERT INTO well_treatments (
    id, well_id, batch_id, micromolar_dose
) VALUES (
    1, 1, 1, 100
);

INSERT INTO suppliers(
    id, name, description
) VALUES (
    4, 'supplier_guy_three', 'decent supplier'
);

INSERT INTO plates(
    id, plate_type_id, person_plated_id, datetime_plated
) VALUES (
    5, 3, 1, '2019-04-10 13:18:20'
);

INSERT INTO plate_types(
    id, name, supplier_id, part_number, n_rows, n_columns, well_shape, opacity
) VALUES (
    4, 'plate_four', 3, NULL, 8, 12, 'round', 'transparent'
);

INSERT INTO submission_records (
id, submission_id, status, sauron_id, datetime_modified
) VALUES (
    2, 1, 'uploaded', 1, now()
);

INSERT INTO sauron_configs (
    id, sauron_id, datetime_changed, description
) VALUES (
    4, 2, '2019-04-11 11:11:11', 'hello'
);

INSERT INTO saurons(
    id, name, active
) VALUES (
    5, 'sauron5', '1'
);

INSERT INTO experiments(
    id, name, description, creator_id, project_id, battery_id, template_plate_id, transfer_plate_id,
    default_acclimation_sec, notes, active
) VALUES (
    5, 'exp 5', 'this is exp 5', 4, 1, 2, 3, 3, 100, 'hi this notes for exp 5', 1
);

INSERT INTO project_types (
    id, name, description
) VALUES (
    4, 'project_four', 'this is project four '
);

INSERT INTO batteries(
    id, name, description, length, author_id, template_id, hidden, notes, assays_sha1
) VALUES (
    4, 'battery_four', 'this is battery four', 1000, 4, 3, 0, 'interesting stuff', cast('assay_four' as binary(20))
);

INSERT INTO assay_positions(
    id, assay_id, battery_id, start
) VALUES(
    4, 5, 4, 0
);

INSERT INTO template_plates (
    id, name, description, plate_type_id, author_id, hidden, created, specializes
) VALUES (
    5, 'template_plate_five', 'this is the fifth tempPlate', 3, 4, 0, now(), NULL
);

INSERT INTO transfer_plates (
    id, name, description, plate_type_id, supplier_id, parent_id, dilution_factor_from_parent, initial_ul_per_well,
    creator_id, datetime_created
) VALUES (
    4, 'transfer_plate_four', 'this is the fourth template plate', 4, NULL, NULL, NULL, 10, 4, now()
);

INSERT INTO compound_labels (
    id, compound_id, name, ref_id
) VALUES (
    3, 3, 'compound_three', 3
);
