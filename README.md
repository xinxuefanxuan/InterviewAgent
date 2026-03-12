# InterviewAgent

面试模拟 Agent（可扩展版）：支持 **PDF 简历解析 -> PlanAgent 生成面试计划 -> 多轮问答 -> SummaryAgent 评分复盘**，并接入了你要求的 **STT/TTS + Kimi2.5 LLM 调用链**。

## 1. 架构概览

- `InterviewAgent`：会话编排，控制面试状态推进。
- `PlanAgent`：支持 LLM 生成结构化面试计划（含问题序列）。
- `SummaryAgent`：支持 LLM 生成评分、优势、短板、建议。
- `WebSearchTool`：可替换的搜索工具层。
- `STT`：Whisper / FunASR。
- `TTS`：Edge-TTS / 火山引擎 / 腾讯云。

## 2. 目录结构

```text
app/main.py                 # FastAPI API（含 STT/TTS 接口）
interview_agent/config.py   # 环境变量配置
interview_agent/core.py     # InterviewAgent 编排
interview_agent/models.py   # 数据模型
llm/client.py               # OpenAI-compatible LLM 客户端（可接 Kimi）
services/stt.py             # Whisper/FunASR
services/tts.py             # Edge/Volc/Tencent TTS
tools/plan_agent.py         # LLM + 规则 fallback 的面试规划
tools/summary_agent.py      # LLM + 规则 fallback 的复盘总结
prompts/plan_prompt.txt     # PlanAgent 系统提示词
prompts/summary_prompt.txt  # SummaryAgent 系统提示词
```

## 3. Kimi2.5 接入（你填 key 即可）

> Kimi 接口是 OpenAI-compatible，这里已按兼容方式接好。

设置环境变量：

```bash
export LLM_ENABLED=true
export LLM_API_KEY="<YOUR_KIMI_API_KEY>"
export LLM_BASE_URL="https://api.moonshot.cn/v1"
export LLM_MODEL="kimi-k2-0905-preview"
```

> 说明：`LLM_API_KEY`、`LLM_MODEL` 你按自己账号可用模型填。

## 4. STT 配置（Whisper / FunASR）

### 4.1 Whisper（API）

```bash
export STT_PROVIDER=whisper
export WHISPER_API_KEY="<YOUR_WHISPER_KEY>"
export WHISPER_BASE_URL="https://api.openai.com/v1"   # 或你的兼容服务
export WHISPER_MODEL="whisper-1"
```

### 4.2 FunASR（本地）

```bash
export STT_PROVIDER=funasr
```

> FunASR 走本地推理，首次加载模型会慢一些。

## 5. TTS 配置（Edge / 火山 / 腾讯）

### 5.1 Edge-TTS（默认）

```bash
export TTS_PROVIDER=edge
export EDGE_TTS_VOICE="zh-CN-XiaoxiaoNeural"
```

### 5.2 火山引擎 TTS

```bash
export TTS_PROVIDER=volc
export VOLC_TTS_ENDPOINT="<VOLC_HTTP_ENDPOINT>"
export VOLC_APP_ID="<APP_ID>"
export VOLC_ACCESS_TOKEN="<ACCESS_TOKEN>"
export VOLC_VOICE_TYPE="zh_female_qingxin"
```

### 5.3 腾讯云 TTS

```bash
export TTS_PROVIDER=tencent
export TENCENT_SECRET_ID="<SECRET_ID>"
export TENCENT_SECRET_KEY="<SECRET_KEY>"
export TENCENT_REGION="ap-beijing"
export TENCENT_VOICE_TYPE=101001
```

## 6. 启动方式

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 7. API

### 7.1 健康检查

```bash
curl http://127.0.0.1:8000/health
```

会返回当前 STT/TTS/LLM 状态。

### 7.2 创建面试 Session（上传 PDF）

```bash
curl -X POST "http://127.0.0.1:8000/session/start" \
  -F "role_hint=Backend Engineer" \
  -F "resume_pdf=@./your_resume.pdf"
```

### 7.3 文本回答

```bash
curl -X POST "http://127.0.0.1:8000/session/answer" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<session_id>","answer_text":"这是我的回答"}'
```

### 7.4 语音回答（STT）

```bash
curl -X POST "http://127.0.0.1:8000/session/answer_audio" \
  -F "session_id=<session_id>" \
  -F "answer_audio=@./answer.wav"
```

### 7.5 文本转语音（TTS）

```bash
curl -X POST "http://127.0.0.1:8000/speech/tts" \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，欢迎来到模拟面试"}' \
  --output tts.mp3
```

### 7.6 面试结束总结

```bash
curl -X POST "http://127.0.0.1:8000/session/complete" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<session_id>"}'
```

## 8. 关键实现说明

1. PlanAgent / SummaryAgent 都是 **LLM 优先，失败自动 fallback 到规则逻辑**，保证服务稳定。
2. LLM 输出强制 JSON，通过 `prompts/*.txt` 可直接调优提示词。
3. STT/TTS 通过 provider 抽象，后续扩展新的云厂商只需加一个服务类。

## 9. 你下一步怎么接前端

你前端只需要：
- 上传 PDF 调 `/session/start`
- 麦克风录音后传 `/session/answer_audio`
- 把返回的下一题文本送到 `/speech/tts` 播放
- 最后调 `/session/complete` 展示报告

这样就能形成完整「语音面试闭环」。
