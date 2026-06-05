# 数据字典 (Data Dictionary)

| 字段名称 (Field Name) | 数据类型 (Type) | 描述 (Description) | 来源 (Source) | 备注 (Notes) |
| :--- | :--- | :--- | :--- | :--- |
| **patient_name** | String | 患者全名 | OCR / 输入 | 用于文件匹配和标识 |
| **cobb_angle** | Float | Cobb 角 (度) | OCR / 计算 | 评估脊柱侧弯严重程度的关键指标 |
| **vertebral_rotation**| List[Float] | 椎体旋转角度 | 计算 / 估算 | 长度通常为 17 (T1-L5) |
| **coronal_offset** | List[Float] | 冠状面偏移 (mm) | 计算 / 估算 | 椎体中心偏离中线的距离 |
| **treatment_type** | Enum | 治疗类型 | 用户输入 | Values: Brace (支具), Surgery (手术), Observation (观察) |
| **compliance** | Float | 依从性 | 用户输入 | 范围 0.0 - 1.0，反映患者佩戴支具的执行度 |
| **duration** | Integer | 持续时间 (月) | 用户输入 | 模拟预测的时间跨度 |
| **evolution_series** | List[Object] | 演变序列 | 模拟输出 | 包含按周或月的时间步长数据 |
| **week** | Integer | 周索引 | 模拟输出 | 从 0 开始，表示模拟进行的周数 |
| **predicted_cobb** | Float | 预测 Cobb 角 | 模拟输出 | 该时间步长的预测角度 |
| **metrics** | Object | 关键指标 | 患者服务 | 包含 cobb_angle, kyphosis_max, lordosis_max 等 |
| **curve_data** | Object | 详细曲线数据 | 患者服务 | 包含 vertebral_rotation, coronal_offsets, sagittal_profile |
| **timeline** | List[Object] | 时间轴数据 | 模拟服务 | 包含每周的 control (对照组) 和 intervention (干预组) 数据 |
