from chemfish.core._imports import *
from chemfish.core.data_generations import *
from chemfish.core.valar_singleton import *


@abcd.internal
class InternalValarTools:
    """
    A collection of utility functions for internal use in Chemfish that are specific to the data in Valar.
    Equivalents of some of these functions are in the external-use ValarTools class, which delegates to this class.
    """

    @classmethod
    def download_frame_timestamps(cls, run_id: int) -> np.array:
        """
        Downloads the timestamps that SauronX recorded for the frame capture times, or None if the sensor was not defined.
        Will always return None for legacy data.
        In pre-PointGrey data, these are the timestamps that MATLAB received the frames.
        In PointGrey data, these are the timestamps that the image was taken (according to the camera firmware).
        :param run_id: The ID of a runs row, only
        :return: The numpy array of floats, or None
        """
        return InternalValarTools.convert_sensor_data(
            SensorData.select()
            .where(SensorData.run_id == run_id)
            .where(SensorData.sensor_id == 3)
            .first()
        )

    @classmethod
    def download_stimulus_timestamps(cls, run_id: int) -> Optional[np.array]:
        """
        Downloads the timestamps that SauronX recorded for the stimuli, or None if the sensor was not defined.
        Will always return None for legacy data.
        :param run_id: The ID of a runs row, only
        :return: The numpy array of floats, or None
        """
        return InternalValarTools.convert_sensor_data(
            SensorData.select()
            .where(SensorData.run_id == run_id)
            .where(SensorData.sensor_id == 4)
            .first()
        )

    @classmethod
    def convert_sensor_data(cls, data: SensorData) -> Union[None, np.array, bytes, str]:
        """
        Downloads and converts sensor data.
        See `InternalValarTools.convert_sensor_data_from_bytes` for details.
        :param data: The ID or instance of a row in sensor_data
        :return: The converted data
        """
        data = SensorData.fetch(data)
        return InternalValarTools.convert_sensor_data_from_bytes(data.sensor, data.floats)

    @classmethod
    def convert_sensor_data_from_bytes(
        cls, sensor: Union[str, int, Sensors], data: bytes
    ) -> Union[None, np.array, bytes, str]:
        """
        Convert the sensor data to its appropriate type as defined by `sensors.data_type`.
        WARNING:
            Currently does not handle `sensors.data_type=='utf8_char'`. Currently there are no sensors in Valar with this data type.
        :param sensor: The name, ID, or instance of the sensors row
        :param data: The data from `sensor_data.floats`; despite the name this is blob represented as bytes and may not correspond to floats at all
        :return: The converted data, or None if `data` is None
        """
        sensor = Sensors.fetch(sensor)
        dt = sensor.data_type
        if data is None:
            return None
        if dt == "byte":
            return np.frombuffer(data, dtype=np.byte)
        if dt == "unsigned_byte":
            return np.frombuffer(data, dtype=np.byte) + 2 ** 7
        if dt == "short":
            return np.frombuffer(data, dtype=">i2").astype(np.int64)
        if dt == "unsigned_short":
            return np.frombuffer(data, dtype=">i2").astype(np.int64) + 2 ** 15
        if dt == "int":
            return np.frombuffer(data, dtype=">i4").astype(np.int64)
        if dt == "unsigned_int":
            return np.frombuffer(data, dtype=">i4").astype(np.int64) + 2 ** 31
        if dt == "float":
            return np.frombuffer(data, dtype=">f4").astype(np.float64)
        if dt == "double":
            return np.frombuffer(data, dtype=">f8").astype(np.float64)
        if dt == "utf8_char":
            return str(dt, encoding="utf-8")
        elif dt == "other":
            return data
        else:
            raise UnsupportedOpError("Oh no! Sensor cache doesn't recognize dtype {}".format(dt))


__all__ = ["InternalValarTools"]
