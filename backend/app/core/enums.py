from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"
    ENGINEER = "ENGINEER"
    VIEWER = "VIEWER"


class ProjectStatus(StrEnum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    ACCEPTED = "ACCEPTED"
    ARCHIVED = "ARCHIVED"


class SampleType(StrEnum):
    CONCRETE = "CONCRETE"
    STEEL = "STEEL"
    SOIL = "SOIL"
    MORTAR = "MORTAR"
    ASPHALT = "ASPHALT"


class SampleStatus(StrEnum):
    PENDING = "PENDING"
    TESTING = "TESTING"
    DONE = "DONE"


class TestConclusion(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class TestRule(StrEnum):
    GTE = "GTE"
    LTE = "LTE"


class AiLevel(StrEnum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class AiTaskStatus(StrEnum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class AiPhase(StrEnum):
    FEASIBILITY = "FEASIBILITY"
    REQUIREMENTS = "REQUIREMENTS"
    ARCHITECTURE = "ARCHITECTURE"
    DETAILED_DESIGN = "DETAILED_DESIGN"
    IMPLEMENTATION = "IMPLEMENTATION"
    MAINTENANCE = "MAINTENANCE"


class DefectSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    TRIVIAL = "TRIVIAL"


class DefectStatus(StrEnum):
    OPEN = "OPEN"
    FIXED = "FIXED"


ROLE_LABELS = {"ADMIN": "管理员", "ENGINEER": "检测工程师", "VIEWER": "查阅人员"}
PROJECT_STATUS_LABELS = {
    "PLANNING": "筹备中",
    "IN_PROGRESS": "进行中",
    "ACCEPTED": "已验收",
    "ARCHIVED": "已归档",
}
SAMPLE_TYPE_LABELS = {
    "CONCRETE": "混凝土试块",
    "STEEL": "钢筋",
    "SOIL": "土工样品",
    "MORTAR": "砂浆试块",
    "ASPHALT": "沥青混合料",
}
SAMPLE_STATUS_LABELS = {"PENDING": "待检", "TESTING": "检测中", "DONE": "已完成"}
CONCLUSION_LABELS = {"PASS": "合格", "FAIL": "不合格"}
AI_PHASE_LABELS = {
    "FEASIBILITY": "可行性分析",
    "REQUIREMENTS": "需求分析",
    "ARCHITECTURE": "总体设计",
    "DETAILED_DESIGN": "详细设计",
    "IMPLEMENTATION": "实现与测试",
    "MAINTENANCE": "维护复盘",
}
AI_LEVEL_LABELS = {"L1": "L1 自动完成", "L2": "L2 人机协作", "L3": "L3 纯人工"}
AI_STATUS_LABELS = {"SUCCESS": "成功", "PARTIAL": "部分可用", "FAILED": "失败"}
DEFECT_SEVERITY_LABELS = {
    "CRITICAL": "致命",
    "MAJOR": "严重",
    "MINOR": "一般",
    "TRIVIAL": "轻微",
}
DEFECT_STATUS_LABELS = {"OPEN": "待修复", "FIXED": "已修复"}
