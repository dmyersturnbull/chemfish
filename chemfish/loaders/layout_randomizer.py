from kale.core.core_imports import *


class MissingFieldError(MissingResourceError):
    pass


class LayoutRandomizer:
    def _check_md(self, metadata: Dict[str, str]):
        """
        Checks provided metadata (to be used for new template plate) and makes sure it is valid.
        Must have 'name' and 'desc' key.
        """
        missing = None
        if "name" not in metadata:
            missing = "name"
        if "desc" not in metadata:
            missing = "desc"
        if missing:
            raise MissingFieldError("Field '{}' is missing in metadata dictionary".format(missing))

    def _gen_tw_dict(self, tp_id: int, well_parser: Union[WB0, WB1]):
        """
        Generates dictionary of template wells that will be shuffled.
        """
        t_wells = [
            w for w in TemplateWells.select().where(TemplateWells.template_plate_id == tp_id)
        ]
        tw_dict = {}
        for t in t_wells:
            for i in well_parser.parse(t.well_range_expression):
                tw_dict[i] = {
                    "age_expression": t.age_expression,
                    "control_type": t.control_type,
                    "group_expression": t.group_expression,
                    "n_expression": t.n_expression,
                    "variant_expression": t.variant_expression,
                }
        return tw_dict

    def _gen_tt_dict(self, tp_id: int, well_parser: Union[WB0, WB1]):
        """
        Generates dictionary of template treatments that will be shuffled. Separate from
        _gen_tw_dict as it's possible for template_treatment well_range_expressions to differ
        from well_range_expressions of template_wells.
        """
        t_treats = [
            tt
            for tt in TemplateTreatments.select().where(
                TemplateTreatments.template_plate_id == tp_id
            )
        ]
        tt_dict = {}
        for tt in t_treats:
            for i in well_parser.parse(tt.well_range_expression):
                # Replace position specific parameters in dose_exression (e.g: $r & $c)
                r, c = well_parser.label_to_rc(i)
                fixed_dose_exp = tt.dose_expression.replace("$r", str(r)).replace("$c", str(c))
                tt_dict[i] = {
                    "batch_expression": tt.batch_expression,
                    "dose_expression": fixed_dose_exp,
                }
        return tt_dict

    def _insert_t_wells(self, tw_dict, well_idx, tp, well_parser: Union[WB0, WB1]):
        """
        Inserts Template Wells.
        """
        new_t_wells = []
        for idx, w in enumerate(well_idx):
            w_lab = well_parser.index_to_label(w)
            ref_w = tw_dict[w_lab]
            new_tw = {
                "age_expression": ref_w["age_expression"],
                "control_type": ref_w["control_type"],
                "group_expression": ref_w["group_expression"],
                "n_expression": ref_w["n_expression"],
                "template_plate": tp,
                "variant_expression": ref_w["variant_expression"],
                "well_range_expression": well_parser.index_to_label(idx + 1),
            }
            new_t_wells.append(new_tw)
        TemplateWells.insert_many(new_t_wells).execute()

    def _insert_t_treatments(self, tt_dict, well_idx, tp, well_parser: Union[WB0, WB1]):
        """
        Inserts Template Treatments.
        """
        new_t_treatments = []
        for idx, w in enumerate(well_idx):
            w_lab = well_parser.index_to_label(w)
            ref_tt = tt_dict[w_lab]
            new_tt = {
                "batch_expression": ref_tt["batch_expression"],
                "dose_expression": ref_tt["dose_expression"],
                "template_plate": tp,
                "well_range_expression": well_parser.index_to_label(idx + 1),
            }
            new_t_treatments.append(new_tt)
        TemplateTreatments.insert_many(new_t_treatments).execute()

    def randomize(
        self, tp_id: TempPlateLike, new_metadata: Dict[str, str], output_mapping: bool = True
    ):
        """
        Generates a randomized layout based on a template_plate id. Inserts it into the database with the provided
        metadata.
        :param tp_id: Id of the template_plate you're making a layout out of.
        :param new_metadata: Dictionary containing fields for your new template plate.
        :param output_mapping: if true outputs an excel sheet with the mapping from mother plate to newly created daughter plate.
        :return:
        """
        self._check_md(new_metadata)
        tp = TemplatePlates.fetch(tp_id)
        p_type = tp.plate_type
        new_tp = TemplatePlates(
            author=tp.author,
            description=new_metadata["desc"],
            name=new_metadata["name"],
            plate_type=p_type,
            specializes=tp.id,
        )
        total_wells = p_type.n_columns * p_type.n_rows
        well_idx = np.arange(1, total_wells + 1)
        # shuffle indices of well for randomized layout
        np.random.shuffle(well_idx)
        wb1 = ParsingWB1(p_type.n_rows, p_type.n_columns)
        tw_dict = self._gen_tw_dict(tp.id, wb1)
        tt_dict = self._gen_tt_dict(tp.id, wb1)
        # Add new template_plate
        new_tp.save()
        # Add new template_wells
        self._insert_t_wells(tw_dict, well_idx, new_tp, wb1)
        # Add new template_treatments
        self._insert_t_treatments(tt_dict, well_idx, new_tp, wb1)
        if output_mapping:
            daughter_wells = np.array([wb1.index_to_label(k) for k in well_idx])
            mother_wells = np.array([wb1.index_to_label(i) for i in np.arange(1, 97)])
            mapping_df = pd.DataFrame(mother_wells, daughter_wells).reset_index()
            mapping_df.columns = ["source_well", "target_well"]
            output_file = "mapping_from_{}_to_{}.xlsx".format(tp_id, new_tp.id)
            mapping_df.to_excel(output_file)
            print("Output Mapping file saved as: {}".format(output_file))
        return new_tp, well_idx, tt_dict, tw_dict


__all__ = ["LayoutRandomizer", "MissingFieldError"]
