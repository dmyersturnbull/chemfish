from kale.core.core_imports import *
from kale.model.audio import Waveform


class AudioExpansion:
    @classmethod
    def expand(
        cls,
        stimseries: pd.Series,
        stim: Union[Stimuli, str, int],
        waveform: Waveform,
        is_legacy: bool,
    ) -> np.array:
        """
        Embedds a waveform into a stimframes array.
        :param stimseries:
        :param stim:
        :param waveform:
        :param is_legacy:
        :return:
        """
        stim = Stimuli.fetch(stim)
        logger.info("Expanding audio on {}{}".format(stim.name, "(legacy)" if is_legacy else ""))
        form = (
            waveform.standardize_legacy(50.0, 200.0)
            if is_legacy
            else waveform.standardize_sauronx(50.0, 200.0)
        )
        # noinspection PyTypeChecker
        starts = np.argwhere(stimseries > 0)
        built = []
        i = 0
        for start in starts:
            # if the audio is a block format, start will often be less than i, which is OK
            if i == 0 or start >= i:
                if start < i:
                    raise AlgorithmError("Frame {} went off the edge".format(start))
                built.append(np.zeros(start - i))
                built.append(form.data)
                i = start + len(form.data)
        built.append(np.zeros(len(stimseries) - i))
        return np.concatenate(built)


__all__ = ["AudioExpansion"]
