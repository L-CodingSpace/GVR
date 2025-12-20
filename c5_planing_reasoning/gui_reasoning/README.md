# GUI 视频评估脚本使用说明

## 文件说明

### 1. `gui_eval.json`
配置文件，包含5个GUI任务的评估配置：
- `01`: 复制粘贴邮件任务
- `02`: 点击PDF文件任务
- `03`: 点击PowerPoint对话框OK按钮任务
- `04`: 点击Project文本任务
- `05`: 移动鼠标到暂停图标任务

每个任务包含：
- `input_image_path`: 输入图片路径
- `video_path`: 待评估视频路径
- `i2v_prompt`: 图生视频的提示词
- `eval_task_description`: 评估任务描述（包含评分标准和输出格式）

### 2. `gui_eval.py`
单个任务评估脚本。

**使用方法：**
```bash
# 修改脚本中的 task_id 变量（第25行）
task_id = "01"  # 可选: "01", "02", "03", "04", "05"

# 运行脚本
python3 gui_eval.py
```

### 3. `gui_eval_batch.py`
批量评估所有任务的脚本。

**使用方法：**
```bash
# 直接运行，会自动处理所有任务
python3 gui_eval_batch.py
```

## 输出结果

评估结果会保存在 `analysis_results_gui/` 目录下：

### 单个任务评估输出：
- `[video_name].json`: 评估结果的JSON格式
- `[video_name].txt`: 详细日志（包含完整prompt和结果）

### 批量评估额外输出：
- `batch_summary.json`: 批量处理的汇总报告

## JSON结果格式

```json
{
  "video_meets_requirements": true/false,
  "overall_score": 0.0-1.0,
  "step_by_step_evaluation": {
    "步骤名称": {
      "observed": true/false,
      "comment": "评论"
    }
  },
  "evaluation_summary": "总结"
}
```

## 配置说明

### API密钥
在脚本中配置（第24行）：
```python
API_KEY = "your_api_key_here"
```

### SDK版本
脚本使用新版 `google-genai` SDK：
```python
from google import genai
client = genai.Client(api_key=API_KEY)
```

如果遇到导入错误，请确保安装了正确的SDK：
```bash
pip install google-genai
```

### 模型选择
默认使用 `gemini-2.5-pro`（第69行）：
```python
model_name = "gemini-2.5-pro"
```

## 注意事项

1. 确保视频文件路径正确
2. 视频文件需要存在于 `generated_videos/kling/` 目录下
3. API调用可能需要一些时间，请耐心等待
4. 批量处理会自动清理上传的文件
5. 如果某个任务失败，不会影响其他任务的处理

## 常见问题

**Q: 遇到 `ImportError: cannot import name 'generativeai' from 'google'` 错误？**
A: 请确保安装了正确的SDK版本：
```bash
pip install google-genai
```
不是 `google-generativeai`（旧版）

**Q: 视频文件未找到？**
A: 检查 `gui_eval.json` 中的 `video_path` 是否正确，路径是相对于脚本所在目录的。

**Q: API调用失败？**
A: 检查API密钥是否正确，网络连接是否正常。

**Q: 文件处理超时？**
A: 视频文件可能太大，可以尝试压缩视频或增加 `max_wait_time` 的值。

## 修改历史

- 2024: 创建初始版本
- 修复JSON格式问题（转义字符）
- 适配gui_eval.json配置文件
- 添加批量处理功能

