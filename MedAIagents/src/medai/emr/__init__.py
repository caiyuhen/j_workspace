"""
电子病历 (EMR) 自动化模块
"""

from .automation import MedicalNoteTemplate, EMRInformationExtractor, EMRNoteGenerator, ICD10Coder

__all__ = [
    'MedicalNoteTemplate',
    'EMRInformationExtractor',
    'EMRNoteGenerator',
    'ICD10Coder',
]
