use deku::{DekuContainerWrite, DekuUpdate};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyType};
use pythonize::{depythonize, pythonize};
use rm_referee_protocol::{RefereeFrame, RefereeFrameCmdData, RefereeFrameHeader};

#[pyclass]
pub struct RefereeFrameHeaderPy(RefereeFrameHeader);

#[pyclass]
pub struct RefereeFramePy(RefereeFrame);

#[pymethods]
impl RefereeFrameHeaderPy {
    #[new]
    fn new(data: &pyo3::prelude::Bound<'_, PyBytes>) -> PyResult<Self> {
        let buf = data.as_bytes();
        let header = RefereeFrameHeader::try_from(buf)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse header: {e}")))?;
        Ok(Self(header))
    }

    #[getter]
    fn data_length(&self) -> PyResult<u16> {
        Ok(self.0.data_length)
    }

    #[getter]
    fn seq(&self) -> PyResult<u8> {
        Ok(self.0.seq)
    }

    #[getter]
    fn crc8(&self) -> PyResult<u8> {
        Ok(self.0.crc8)
    }

    fn to_bytes(&self, py: Python) -> PyResult<Py<PyBytes>> {
        let v: Vec<u8> = self
            .0
            .clone()
            .try_into()
            .map_err(|e| PyValueError::new_err(format!("Failed to serialize header: {e}")))?;
        Ok(PyBytes::new(py, &v).into())
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("RefereeFrameHeaderPy({:?})", self.0))
    }
}

#[pymethods]
impl RefereeFramePy {
    #[classmethod]
    fn from_cmd_py(
        _cls: &pyo3::prelude::Bound<'_, PyType>,
        seq: u8,
        cmd: &pyo3::prelude::Bound<'_, PyAny>,
    ) -> PyResult<Self> {
        let cmd_data: RefereeFrameCmdData = depythonize(cmd)
            .map_err(|e| PyValueError::new_err(format!("Failed to depythonize cmd_data: {e}")))?;
        let mut frame = RefereeFrame {
            header: RefereeFrameHeader {
                seq,
                ..Default::default()
            },
            cmd_data,
            frame_tail: 0,
        };
        frame.update().map_err(|e| {
            PyValueError::new_err(format!("Failed to update frame after construction: {e}"))
        })?;
        Ok(Self(frame))
    }

    #[classmethod]
    fn from_cmd_bytes(
        _cls: &pyo3::prelude::Bound<'_, PyType>,
        seq: u8,
        cmd_bytes: &pyo3::prelude::Bound<'_, PyBytes>,
    ) -> PyResult<Self> {
        let buf = cmd_bytes.as_bytes();
        let cmd_data = RefereeFrameCmdData::try_from(buf)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse cmd_data: {e}")))?;
        let mut frame = RefereeFrame {
            header: RefereeFrameHeader {
                seq,
                ..Default::default()
            },
            cmd_data,
            frame_tail: 0,
        };
        frame.update().map_err(|e| {
            PyValueError::new_err(format!("Failed to update frame after construction: {e}"))
        })?;
        Ok(Self(frame))
    }

    #[new]
    fn new(data: &pyo3::prelude::Bound<'_, PyBytes>) -> PyResult<Self> {
        let buf = data.as_bytes();
        let frame = RefereeFrame::try_from(buf)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse frame: {e}")))?;
        Ok(Self(frame))
    }

    #[getter]
    fn header(&self) -> PyResult<RefereeFrameHeaderPy> {
        Ok(RefereeFrameHeaderPy(self.0.header))
    }

    #[getter]
    fn frame_tail(&self) -> PyResult<u16> {
        Ok(self.0.frame_tail)
    }

    #[getter]
    fn seq(&self) -> PyResult<u8> {
        Ok(self.0.header.seq)
    }

    #[setter]
    fn set_seq(&mut self, value: u8) -> PyResult<()> {
        self.0.header.seq = value;
        Ok(())
    }

    fn cmd_data_bytes(&self, py: Python) -> PyResult<Py<PyBytes>> {
        let v = self
            .0
            .cmd_data
            .to_bytes()
            .map_err(|e| PyValueError::new_err(format!("Failed to serialize cmd_data: {e}")))?;
        Ok(PyBytes::new(py, &v).into())
    }

    fn cmd_id(&self) -> PyResult<u16> {
        let v = self
            .0
            .cmd_data
            .to_bytes()
            .map_err(|e| PyValueError::new_err(format!("Failed to serialize cmd_data: {e}")))?;
        if v.len() < 2 {
            return Err(PyValueError::new_err("cmd_data too short to contain id"));
        }
        Ok(u16::from_le_bytes([v[0], v[1]]))
    }

    fn set_cmd_data_bytes(&mut self, data: &pyo3::prelude::Bound<'_, PyBytes>) -> PyResult<()> {
        let buf = data.as_bytes();
        let parsed = RefereeFrameCmdData::try_from(buf)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse cmd_data: {e}")))?;
        self.0.cmd_data = parsed;
        Ok(())
    }

    fn set_header_from_bytes(&mut self, data: &pyo3::prelude::Bound<'_, PyBytes>) -> PyResult<()> {
        let buf = data.as_bytes();
        let header = RefereeFrameHeader::try_from(buf)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse header: {e}")))?;
        self.0.header = header;
        Ok(())
    }

    // Direct Python dict/list bridge using pythonize
    fn cmd_data_py(&self, py: Python) -> PyResult<Py<PyAny>> {
        let obj = pythonize(py, &self.0.cmd_data)
            .map_err(|e| PyValueError::new_err(format!("Failed to pythonize cmd_data: {e}")))?;
        Ok(obj.unbind())
    }

    fn set_cmd_data_py(&mut self, obj: &pyo3::prelude::Bound<'_, PyAny>) -> PyResult<()> {
        let v: RefereeFrameCmdData = depythonize(obj)
            .map_err(|e| PyValueError::new_err(format!("Failed to depythonize cmd_data: {e}")))?;
        self.0.cmd_data = v;
        Ok(())
    }

    fn to_bytes(&self, py: Python) -> PyResult<Py<PyBytes>> {
        let mut frame = self.0.clone();
        frame.update().map_err(|e| {
            PyValueError::new_err(format!("Failed to update frame before serialization: {e}"))
        })?;
        let v: Vec<u8> = frame
            .try_into()
            .map_err(|e| PyValueError::new_err(format!("Failed to serialize frame: {e}")))?;
        Ok(PyBytes::new(py, &v).into())
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("RefereeFramePy({:?})", self.0))
    }
}

#[pymodule]
fn rm_referee_protocol_py(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RefereeFrameHeaderPy>()?;
    m.add_class::<RefereeFramePy>()?;
    Ok(())
}
