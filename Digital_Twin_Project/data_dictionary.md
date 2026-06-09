<<<<<<< HEAD
# 脊柱数字孪生数据字典 (Spine Digital Twin Data Dictionary)

本文档旨在解释 `extracted_data.json` 及 3D 建模系统中使用的各项医学数据指标的含义。

## 1. 核心生物力学参数 (Core Biomechanical Metrics)

这些参数主要用于评估脊柱的整体形态和平衡状态。

| 字段名 (Field) | 中文名称 | 含义与解释 | 正常值参考 |
| :--- | :--- | :--- | :--- |
| **Kyphosis (Max)** | 最大后凸角度 | 通常指胸椎后凸角 (Thoracic Kyphosis)。脊柱胸段向后弯曲的角度。过大可能导致驼背。 | 20° - 40° |
| **Lordosis (Max)** | 最大前凸角度 | 通常指腰椎前凸角 (Lumbar Lordosis)。脊柱腰段向前弯曲的角度。 | 30° - 50° |
| **Coronal Offset** | 冠状面偏移 | 脊柱在左右方向上偏离中心线的最大距离。用于评估身体躯干的侧向平衡。 | < 20mm |
| **Sagittal Offset** | 矢状面偏移 | 脊柱在前后方向上偏离中心垂线的距离 (SVA)。用于评估身体的前倾或后倾状态。 | < 50mm |
| **Vertebral Rotation** | 椎体旋转 | 椎体绕自身垂直轴旋转的角度。这是脊柱侧弯的三维特征之一（不仅侧弯，还伴有旋转）。 | 0° (无旋转) |

## 2. 原始报告术语 (Raw Report Terms)

以下术语直接来源于 PDF 扫描件 OCR 识别结果：

| 原始术语 (Raw Term) | 推测含义 (Inferred Meaning) | 详细说明 |
| :--- | :--- | :--- |
| **ICT** | 髂嵴切线 (Iliac Crest Tangent) / 拐点 | 在脊柱分析中常作为参考基准线，或指代曲线的某些切线特征。 |
| **DL-DR (3D Length)** | 左右背部高差/长度差 | 可能指背部左右两侧表面轮廓的三维距离差，常用于评估“剃刀背”畸形 (Rib Hump)。 |
| **KA (Kyphosis Apex)** | 后凸顶点 | 胸椎后凸曲线的最突点位置（如 T7 或 T8）。 |
| **LA (Lordosis Apex)** | 前凸顶点 | 腰椎前凸曲线的最深点位置（如 L3 或 L4）。 |
| **VP (Vertebra Prominens)** | 隆椎 (C7) | 第7颈椎，颈部最突出的骨点，常作为测量的上端参考点。 |
| **SP (Sacral Promontory)** | 骶骨岬 / 骶骨点 | 骶骨上缘的中心点，常作为测量的下端参考点。 |
| **VPDM** | 垂直偏离距离 | 可能指 VP 点相对于 DM (中线) 的偏移。 |
| **Transversal (level)** | 横断面 (水平面) | 指椎体在水平面上的旋转或位置数据。 |
| **Sagittal** | 矢状面 (侧面) | 指从侧面观察的脊柱形态数据（前凸/后凸）。 |
| **Coronal** | 冠状面 (正面) | 指从正面观察的脊柱形态数据（侧弯）。 |

## 3. 3D 建模映射关系 (3D Model Mapping)

在我们的数字孪生模型中，上述数据被映射为以下几何特征：

*   **X轴 (红色)**: 代表 **冠状面 (Coronal)**。
    *   数据来源：`Coronal Offset` 或由 `Vertebral Rotation` 推导的侧向位移。
    *   *含义*：向左或向右弯曲。
*   **Y轴 (绿色)**: 代表 **矢状面 (Sagittal)**。
    *   数据来源：`Kyphosis` 和 `Lordosis` 角度。
    *   *含义*：向前或向后弯曲（驼背或塌腰）。
*   **Z轴 (蓝色)**: 代表 **轴向 (Axial)**。
    *   数据来源：人体身高模拟 (0-600mm)。
    *   *含义*：脊柱的垂直高度。
*   **节点颜色**:
    *   🟢 **Green**: 正常椎体 (旋转 < 5° 且 偏移 < 10mm)。
    *   🔴 **Red**: 异常椎体 (旋转 > 5° 或 偏移 > 10mm)。

## 4. 常见缩写对照表

*   **T1 - T12**: 胸椎 (Thoracic Vertebrae) 第1至第12节。
*   **L1 - L5**: 腰椎 (Lumbar Vertebrae) 第1至第5节。
*   **C7**: 第7颈椎 (Cervical Vertebra 7)。
*   **S1**: 第1骶椎 (Sacral Vertebra 1)。
=======
# 脊柱数字孪生数据字典 (Spine Digital Twin Data Dictionary)

本文档旨在解释 `extracted_data.json` 及 3D 建模系统中使用的各项医学数据指标的含义。

## 1. 核心生物力学参数 (Core Biomechanical Metrics)

这些参数主要用于评估脊柱的整体形态和平衡状态。

| 字段名 (Field) | 中文名称 | 含义与解释 | 正常值参考 |
| :--- | :--- | :--- | :--- |
| **Kyphosis (Max)** | 最大后凸角度 | 通常指胸椎后凸角 (Thoracic Kyphosis)。脊柱胸段向后弯曲的角度。过大可能导致驼背。 | 20° - 40° |
| **Lordosis (Max)** | 最大前凸角度 | 通常指腰椎前凸角 (Lumbar Lordosis)。脊柱腰段向前弯曲的角度。 | 30° - 50° |
| **Coronal Offset** | 冠状面偏移 | 脊柱在左右方向上偏离中心线的最大距离。用于评估身体躯干的侧向平衡。 | < 20mm |
| **Sagittal Offset** | 矢状面偏移 | 脊柱在前后方向上偏离中心垂线的距离 (SVA)。用于评估身体的前倾或后倾状态。 | < 50mm |
| **Vertebral Rotation** | 椎体旋转 | 椎体绕自身垂直轴旋转的角度。这是脊柱侧弯的三维特征之一（不仅侧弯，还伴有旋转）。 | 0° (无旋转) |

## 2. 原始报告术语 (Raw Report Terms)

以下术语直接来源于 PDF 扫描件 OCR 识别结果：

| 原始术语 (Raw Term) | 推测含义 (Inferred Meaning) | 详细说明 |
| :--- | :--- | :--- |
| **ICT** | 髂嵴切线 (Iliac Crest Tangent) / 拐点 | 在脊柱分析中常作为参考基准线，或指代曲线的某些切线特征。 |
| **DL-DR (3D Length)** | 左右背部高差/长度差 | 可能指背部左右两侧表面轮廓的三维距离差，常用于评估“剃刀背”畸形 (Rib Hump)。 |
| **KA (Kyphosis Apex)** | 后凸顶点 | 胸椎后凸曲线的最突点位置（如 T7 或 T8）。 |
| **LA (Lordosis Apex)** | 前凸顶点 | 腰椎前凸曲线的最深点位置（如 L3 或 L4）。 |
| **VP (Vertebra Prominens)** | 隆椎 (C7) | 第7颈椎，颈部最突出的骨点，常作为测量的上端参考点。 |
| **SP (Sacral Promontory)** | 骶骨岬 / 骶骨点 | 骶骨上缘的中心点，常作为测量的下端参考点。 |
| **VPDM** | 垂直偏离距离 | 可能指 VP 点相对于 DM (中线) 的偏移。 |
| **Transversal (level)** | 横断面 (水平面) | 指椎体在水平面上的旋转或位置数据。 |
| **Sagittal** | 矢状面 (侧面) | 指从侧面观察的脊柱形态数据（前凸/后凸）。 |
| **Coronal** | 冠状面 (正面) | 指从正面观察的脊柱形态数据（侧弯）。 |

## 3. 3D 建模映射关系 (3D Model Mapping)

在我们的数字孪生模型中，上述数据被映射为以下几何特征：

*   **X轴 (红色)**: 代表 **冠状面 (Coronal)**。
    *   数据来源：`Coronal Offset` 或由 `Vertebral Rotation` 推导的侧向位移。
    *   *含义*：向左或向右弯曲。
*   **Y轴 (绿色)**: 代表 **矢状面 (Sagittal)**。
    *   数据来源：`Kyphosis` 和 `Lordosis` 角度。
    *   *含义*：向前或向后弯曲（驼背或塌腰）。
*   **Z轴 (蓝色)**: 代表 **轴向 (Axial)**。
    *   数据来源：人体身高模拟 (0-600mm)。
    *   *含义*：脊柱的垂直高度。
*   **节点颜色**:
    *   🟢 **Green**: 正常椎体 (旋转 < 5° 且 偏移 < 10mm)。
    *   🔴 **Red**: 异常椎体 (旋转 > 5° 或 偏移 > 10mm)。

## 4. 常见缩写对照表

*   **T1 - T12**: 胸椎 (Thoracic Vertebrae) 第1至第12节。
*   **L1 - L5**: 腰椎 (Lumbar Vertebrae) 第1至第5节。
*   **C7**: 第7颈椎 (Cervical Vertebra 7)。
*   **S1**: 第1骶椎 (Sacral Vertebra 1)。
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
