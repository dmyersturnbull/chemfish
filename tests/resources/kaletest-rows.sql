/* 
Sample Insertion SQL Queries to populate kaletest db. Make sure unique keys are different for the values.
*/

#sample users entry
insert into users (id, username, first_name, last_name, write_access, bcrypt_hash) values (4,'test_user7', 'test', 'UserBser', 0, 'jfEHa6wjtC6Fyx95F8miqtgZCSG0V35ZE82EGY3BS5kccr80Y8g3tbTWOzf7');

#sample submission entry
insert into submissions (id, lookup_hash, experiment_id, user_id, person_plated_id, continuing_id, datetime_plated, datetime_dosed, acclimation_sec, description, notes, created) values 
(25, '9p0MKHbf5P3m', 3, 2, 1, 1, '2019-01-26 10:11:12', '2019-01-26 11:11:12', 50, 'this is submission 25', NULL, now())

#sample runs entry
insert into runs (id,experiment_id, plate_id, description, experimentalist_id, submission_id, datetime_run, datetime_dosed, name, tag, sauron_config_id, config_file_id, incubation_min, acclimation_sec, notes) 
values (4,2, 1, 'run number four', 1, 25, '2019-01-28 10:11:12', '2019-01-28 10:42:12', 'run_number_four', 'tag_four', 3, 1, 20, 50, 'hi there r no notes here' );

#sample run_tags entry
insert into run_tags(id,run_id, name, value) values(3,1, 'second run tag', '0abcdefghijklmnop');
insert into run_tags(id,run_id, name, value) values(4,1, 'sauronx_version', '54554512asofja109');

#sample submission_params entry
insert into submission_params(id, submission_id, name, param_type, value) values (5, 2, '$...BC123', 'compound', '\["AB0124403","AB0124404"\]');
insert into submission_params(id, submission_id, name, param_type, value) values (4,1, 'sp_1_7', 'dose', 100);

#sample compound entry
insert into compounds(id, inchi, inchikey, inchikey_connectivity, chembl_id, chemspider_id, smiles) values (3, 'inchi_foo_bar', 'AQWEFNOQVPJJNP-UHFFFAOYSA-N', 'q42345ghijklbs', '113109-290-1', 1101145, 'C=C-B=C-H');

#sample location entry
insert into locations(id, name, description, purpose, part_of, temporary) values(4, 'location_three', 'hello this is location three', 'purpose three', 2, 0);

#sample batches entry
insert into batches(id, lookup_hash, tag, compound_id, made_from_id, supplier_id, ref_id, legacy_internal_id, location_id, box_number, well_number, location_note, amount, concentration_millimolar, solvent_id, molecular_weight, supplier_catalog_number,
person_ordered, date_ordered, notes, suspicious) values (4, '124bff34abagzf', 'wrong_legacy_id_format', 1, NULL,1,1,'BC000040201', 2, 5, 2, 'location three', '200ul', 100, 2, 25.0, 1, 1, now(), 'hello this is notes_six', 1 );

#sample genetic_variants entry
insert into genetic_variants (id, name, mother_id, father_id, lineage_type, date_created, notes, creator_id, fully_annotated) values (4, 'genetic variant four', 7, 5, 'cross', now(), 'notes for gene four', 1, 0);

#sample refs entry
insert into refs (id,name, datetime_downloaded, external_version, description, url) values (4,'ref_four', '2019-01-29 12:48:12', 'ref_four_external_version', 'this is ref four', 'https://www.nonexistentreffour.com');

#sample sensors entry
insert into sensors (id, name, description, data_type, blob_type, n_between) values (4, 'sensor_four', 'this is sensor four.', 'long', 'assay_start', 10);

#sample sensordata entry
insert into sensor_data (id, run_id, sensor_id, floats, floats_sha1) values (5, 2, 3, 1234134093401234987234980721384712934324913448123098409185908135981039581958112379573578136793134696676741671761515747642724576,
cast(2819 as Binary(20)));

#sample control_types entry
insert into control_types (id, name, description, positive, drug_related, genetics_related) values (3,'control type three', 'this is control type three', 1, 1, 1);

#sample wells entry
insert into wells (id,run_id, well_index, control_type_id, variant_id, well_group, n, age) values (9,1, 7, 2,5, 'well group one', 6, 15);

#sample well_features entry 
insert into well_features (id, well_id, type_id, floats, sha1) values (6, 2, 2, 1929014393149134898314981349831498134981341311234143, cast(2111 as Binary(20)));

#sample stimulus entry
insert into stimuli (id, name, default_color, description, analog, rgb, wavelength_nm, audio_file_id) values (3, 'none', 'ffffff', NULL, 1, NULL, NULL, NULL);

#sample stimulus_frames entry
insert into stimulus_frames (id, assay_id, stimulus_id, frames, frames_sha1) values (7, 5, 1, '78654131412341132413409876341324329048132984901238490821394081239080913859018340981349921384', cast(101109 as Binary(20)));

#sample assay entry
insert into assays (id, name, description, length, hidden, template_assay_id, frames_sha1) values (5, 'assay_five', 'this is assay five', 100, 0, 2, cast(122333 as Binary(20)));

#sample well_treatments entry
insert into well_treatments (id, well_id, batch_id, micromolar_dose) values (1, 1, 1,100);

#sample supplier entry
insert into suppliers (id, name, description) values (4, 'supplier_guy_three', 'decent supplier');

#sample plate entry
insert into plates (id, plate_type_id, person_plated_id, datetime_plated) values (5, 3, 1, '2019-04-10 13:18:20');

#sample plate_types entry
insert into plate_types(id, name, supplier_id, part_number,n_rows,n_columns, well_shape, opacity) values (4, 'plate_four', 3, NULL, 8, 12, 'round', 'transparent');

#sample submission_records entry
insert into submission_records (id,submission_id, status, sauron_id, datetime_modified) values (2,1,'uploaded', 1, now());

#sample sauron_configs entry
insert into sauron_configs (id, sauron_id, datetime_changed, description) values (4, 2, '2019-04-11 11:11:11', 'hello');

#sample sauron entry 
insert into saurons (id,name,active) values (5,'sauron5','1');

#sample experiments entry
insert into experiments (id, name, description, creator_id, project_id, battery_id, template_plate_id, transfer_plate_id, default_acclimation_sec,notes, active) values (5, 'exp 5', 'this is exp 5', 4,1,2,3,3,100,'hi this notes for exp 5',1);

#sample project_types entry
insert into project_types (id, name, description) values (4, 'project_four', 'this is project four ');

#sample batteries entry
insert into batteries (id, name, description, length, author_id, template_id,hidden, notes, assays_sha1) values (4, 'battery_four', 'this is battery four', 1000, 4, 3, 0, 'interesting stuff', cast('assay_four' as binary(20)));

#sample template_plates entry 
insert into template_plates (id,name,description, plate_type_id, author_id, hidden,created,specializes) values (5, 'template_plate_five', 'this is the fifth tempPlate', 3, 4, 0, now(),NULL);

#sample transfer_plates entry
insert into transfer_plates (id, name, description, plate_type_id,supplier_id,parent_id, dilution_factor_from_parent, initial_ul_per_well,creator_id, datetime_created) values (4, 'transfer_plate_four', 'this is the fourth template plate',
4, NULL, NULL, NULL, 10, 4, now());

#sample compound_labels entry
insert into compound_labels (id, compound_id, name, ref_id) values (3, 3, 'compound_three',3);