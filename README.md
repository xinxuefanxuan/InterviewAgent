# InterviewAgent

一个可扩展的面试模拟 Agent 原型：支持 **简历 PDF 解析 -> 面试流程规划 -> 多轮问答 -> 面试总结评分**。

## 目标工作流

1. 面试者上传 PDF 简历。
2. `InterviewAgent` 调用 `PlanAgent` 解析候选人信息并生成面试计划。
3. 面试过程以多轮问答进行（当前 API 为文本接口，可无缝接入语音）。
4. 结束后 `SummaryAgent` 输出评分、优势、短板和改进建议。
5. `WebSearchTool` 提供行业趋势或知识补充能力。

## 当前实现（MVP）

### Agent 架构

- `InterviewAgent`：总控编排，管理 session 和面试状态。
- `PlanAgent`：提取话题、推断候选人级别、生成问题序列。
- `SummaryAgent`：对多轮回答进行打分汇总并输出建议。
- `WebSearchTool`：搜索工具抽象（当前是 mock，可替换真实 API）。

### 模块结构

```text
app/main.py                 # FastAPI API
interview_agent/core.py     # InterviewAgent 编排逻辑
interview_agent/models.py   # 数据模型
tools/plan_agent.py         # 规划 agent
tools/summary_agent.py      # 总结 agent
tools/websearch.py          # 搜索工具抽象
```

## API 使用

### 1) 启动服务

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) 创建面试 Session（上传简历 PDF）

```bash
curl -X POST "http://127.0.0.1:8000/session/start" \
  -F "role_hint=Backend Engineer" \
  -F "resume_pdf=@./your_resume.pdf"
```

返回示例：

```json
{
  "session_id": "...",
  "role": "Backend Engineer",
  "candidate_level": "Mid",
  "key_topics": ["python", "cloud"],
  "question": "请你先做一个 1 分钟自我介绍..."
}
```

### 3) 提交回答

```bash
curl -X POST "http://127.0.0.1:8000/session/answer" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<session_id>","answer_text":"这里是候选人的回答"}'
```

### 4) 获取面试总结

```bash
curl -X POST "http://127.0.0.1:8000/session/complete" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<session_id>"}'
```

## 语音能力接入建议（你设想的 STT/TTS）

当前后端已经把核心流程抽象好，接语音时只需新增工具层：

- `SpeechToTextTool`（ASR）：把面试者语音转为 `answer_text`。
- `TextToSpeechTool`（TTS）：把 Agent 生成的题目/反馈转语音播放。

推荐增加两个接口：

- `POST /session/answer_audio`：上传音频 -> ASR -> 复用 `/session/answer`。
- `POST /session/question_audio`：将下一题文本转语音返回音频 URL/bytes。

## 下一步可增强

1. 接入真实 LLM（OpenAI/本地模型）替换规则打分与固定提问。
2. 接入真实 Web 搜索（Tavily/SerpAPI/Bing）。
3. 增加面试官风格（压力面、温和面、技术深挖）。
4. 增加评分维度：表达、技术深度、业务理解、结构化、抗压。
5. 持久化（Redis/Postgres）以支持长期训练数据积累。

---

如果你愿意，我可以在这个基础上继续直接帮你实现：

- Whisper/FunASR 的 `STT` 接入
- Edge-TTS/火山引擎/腾讯云 的 `TTS` 接入
- 真正可跑的 `PlanAgent + SummaryAgent` LLM 提示词和调用链
