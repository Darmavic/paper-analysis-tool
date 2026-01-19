# AutoDL 更新和运行指令

## 步骤1：手动更新代码（因为GitHub连接被阻）

在AutoDL终端执行：

```bash
cd ~/paper-analysis-tool

# 手动更新 analyze_paper.py 中的错误处理代码
# 在第496行后添加JSONDecodeError处理

# 方法1：使用vim编辑
vim scripts/analyze_paper.py
# 找到第500行的 "except Exception as e:"
# 在它之前插入以下内容：
```

插入的内容：
```python
        except json.JSONDecodeError as e:
            # Special handling for JSON parsing errors
            wait_time = base_delay * (2 ** retries)
            print(f"⚠️  JSON解析错误 (API可能返回了非JSON响应). 等待 {wait_time} 秒后重试... (尝试 {retries+1}/{max_retries})")
            print(f"   错误详情: {str(e)[:200]}")
            time.sleep(wait_time)
            retries += 1
            if retries >= max_retries:
                print(f"❌ JSON解析错误持续出现，已达到重试上限。跳过此问题。")
                return None  # Return None to allow skipping
```

在第792行后添加None检查：
```python
            # Handle case where API call failed after max retries
            if response is None:
                print(f"⚠️  API调用失败，跳过此问题")
                return f"# {sub_question.question}\n\n**[分析跳过：API调用失败]**\n\n该问题因API错误被跳过，请稍后手动补充分析。"
```

## 步骤2：或者直接从本地上传修改后的文件

使用AutoDL Web界面上传本地的 `scripts/analyze_paper.py` 文件覆盖远程版本。

## 步骤3：重新运行分析

```bash
cd ~/paper-analysis-tool
source .venv/bin/activate
export HF_ENDPOINT=https://www.modelscope.cn
python scripts/analyze_paper.py --pdf Yang_Shadlen_2007.pdf --vault output
```

## 新功能说明

1. **JSONDecodeError 重试**：遇到JSON解析错误时，会以指数退避方式重试（2秒、4秒、8秒...）
2. **自动跳过**：15次失败后自动跳过该问题，继续处理下一个
3. **详细日志**：打印错误详情帮助诊断问题
4. **优雅降级**：跳过的问题会留下占位符，方便后续手动补充
