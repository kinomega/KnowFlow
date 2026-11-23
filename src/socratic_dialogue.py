# -*- coding: utf-8 -*-
"""
苏格拉底对话模块
通过提问引导用户深入理解概念
"""
from typing import List, Dict, Optional
from .llm_client import LLMClient


class SocraticDialogue:
    """苏格拉底对话引擎"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def _read_answer_file(self) -> Optional[str]:
        """读取桌面md目录下的md文件"""
        from pathlib import Path

        # 获取桌面md目录路径
        desktop = Path.home() / "Desktop" / "md"

        if not desktop.exists():
            print(f"❌ 目录不存在: {desktop}")
            return None

        # 让用户输入文件名，不输入默认answer.md
        filename = input("  请输入文件名（直接Enter默认answer.md）: ").strip()
        if not filename:
            filename = 'answer.md'

        answer_file = desktop / filename

        try:
            if answer_file.exists():
                content = answer_file.read_text(encoding='utf-8')
                return content.strip()
            else:
                print(f"❌ 文件不存在: {filename}")
                return None
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return None

    def start_dialogue(self, concept: str, domain: str = "") -> Dict:
        """
        开始苏格拉底对话

        Args:
            concept: 要理解的概念
            domain: 领域上下文

        Returns:
            dict: {
                "user_understanding": "用户的理解",
                "standard_definition": "标准定义",
                "key_supplements": ["补充1", "补充2"]
            }
        """
        print(f"\n💭 苏格拉底对话模式")
        print(f"📌 概念：{concept}")
        print("=" * 60)

        # 收集用户理解
        user_responses = []
        round_count = 0

        print("\n请说说你对这个概念的理解：")
        print("(输入你的想法，可以是定义、例子、应用场景等)")
        print("(输入 'q' 结束对话，输入 'md' 读取桌面md目录下的文件)\n")

        user_input = input("> ").strip()

        # 支持读取文件
        if user_input.lower() == 'md':
            user_input = self._read_answer_file()
            if not user_input:
                print("❌ 读取失败，请重新输入")
                return None
            print(f"✅ 已读取文件（前200字）:\n{user_input[:200]}...")

        if not user_input or user_input.lower() == 'q':
            print("❌ 已取消")
            return None

        user_responses.append(user_input)

        # 对话循环（无轮数限制，由用户决定结束）
        while True:
            round_count += 1

            # LLM分析用户理解并提问
            question = self._generate_question(
                concept=concept,
                domain=domain,
                user_responses=user_responses,
                round=round_count
            )

            if not question:
                # LLM中断或失败，询问是否重试
                retry = input("\nLLM中断或失败，是否重试？[y/n]: ").strip().lower()
                if retry == 'y':
                    round_count -= 1  # 重试当前轮
                    continue
                else:
                    break

            # 显示对话
            print("\n" + "-" * 40)
            print(f"对话{round_count}")
            print("-" * 40)
            print(f"\n{question}")

            # 用户输入（输入q结束，输入done完成理解）
            user_input = input("> ").strip()

            # 支持读取文件
            if user_input.lower() == 'md':
                user_input = self._read_answer_file()
                if not user_input:
                    print("❌ 读取失败，请重新输入")
                    continue
                print(f"✅ 已读取文件")

            if not user_input or user_input.lower() in ['q', 'done', '完成']:
                if user_input.lower() in ['done', '完成']:
                    print("\n✅ 理解完成！")
                break

            # 支持追加上一轮回答（以+开头）
            if user_input.startswith('+') and user_responses:
                supplement = user_input[1:].strip()
                if supplement:
                    user_responses[-1] += " " + supplement
                    print(f"✅ 已追加到上一轮回答")
                    round_count -= 1  # 重新生成这一轮
                    continue
                else:
                    print("❌ 补充内容为空")
                    continue

            user_responses.append(user_input)

        # 生成最终总结
        print("\n📝 正在整理你的理解...")
        result = self._generate_summary(
            concept=concept,
            domain=domain,
            user_responses=user_responses
        )

        return result

    def _generate_question(self, concept: str, domain: str,
                          user_responses: List[str], round: int) -> Optional[str]:
        """生成引导性问题"""

        system_prompt = """你是苏格拉底式对话的引导者。
通过提问帮助用户深入思考，而不是直接告诉答案。

**但要保持灵活**：
- 如果用户明确表示"一无所知"或"需要基本概念"，先提供简洁的基础解释（2-3句话）
- 有了基础后，再转入提问式引导
- 不要僵化地拒绝解释

每轮回复必须包含：
1. **分析**：简洁指出用户回答的准确之处和不准确之处
2. **修正/解释**：如果有误解，直接指出正确理解；如果缺乏基础，先给基本概念
3. **追问**：引导更深入思考的问题

要求：
- 先分析再提问
- 不准确的地方要明确指出并修正
- 保持客观、简洁
- 不要夸大、不要虚假肯定
- 灵活应对用户需求，不要死板"""

        domain_hint = f"\n领域：{domain}" if domain else ""

        # 构建对话历史
        history = "\n".join([f"用户回答{i+1}：{resp}"
                            for i, resp in enumerate(user_responses)])

        prompt = f"""概念：{concept}{domain_hint}

{history}

作为引导者，你的任务：
1. **简洁分析**用户最新回答的准确性（1-2句话）
2. **直接修正**不准确的理解（如有）
3. **判断**是否已经理解到位
4. **继续提问**引导更深入思考

回复格式：
[分析] 你的回答...（准确/不准确之处）
[修正]（如有误解）正确的理解应该是...
[追问] 那么...？

**标注要求**：
- 当你给出的修正、解释或补充**没有明确事实依据**时，在该句末尾标注`[推测]`
- 例如："这可能是因为...`[推测]`"
- 只标注推测部分，有依据的不标注
- 保持简洁，不要过度标注

其他要求：
- 每轮必须有分析和修正（如需要）
- 不准确的地方要明确指出
- 保持客观、简洁
- 不要夸大、不要虚假肯定
- 理解到位后可以说"理解基本到位"，但仍提供可选深入方向

你的回应："""

        response = self.llm.generate(prompt, system_prompt)
        return response.strip() if response else None

    def _generate_summary(self, concept: str, domain: str,
                         user_responses: List[str]) -> Dict:
        """生成最终总结（JSON结构化输出）"""

        import json

        system_prompt = "你是知识整理助手，客观、准确、简洁。请严格按照JSON格式输出。"

        domain_hint = f"\n领域：{domain}" if domain else ""

        # 构建对话历史
        history = "\n".join([f"- {resp}" for resp in user_responses])

        # 智能压缩策略：判断用户理解是否需要压缩
        total_length = sum(len(resp) for resp in user_responses)
        need_compress = len(user_responses) > 1 and total_length > 500

        # 根据是否需要压缩，设置不同的要求
        if need_compress:
            user_understanding_req = "整合用户多轮回答，提炼核心要点，去掉重复和冗余"
        else:
            user_understanding_req = "整合用户回答，保持完整内容"

        prompt = f"""概念：{concept}{domain_hint}

用户在对话中的理解：
{history}

请生成JSON格式的总结，严格遵循以下结构：

{{
  "concept": "{concept}",
  "domain": "{domain if domain else ''}",
  "standard_definition": {{
    "core": "核心定义（1-2句话，精准概括）",
    "description": "详细描述（展开说明，不少于300字，涵盖概念内涵、发展历史、核心机制等）",
    "key_points": [
      "关键点1：xxx",
      "关键点2：xxx",
      "关键点3：xxx"
    ],
    "use_cases": [
      "应用场景1",
      "应用场景2"
    ],
    "related_concepts": ["相关概念1", "相关概念2"]
  }},
  "user_understanding": {{
    "content": "用户理解内容（{user_understanding_req}，用第一人称'我'）",
    "compressed": {str(need_compress).lower()}
  }},
  "key_supplements": [
    "用户遗漏的重点1（如果用户理解完整就返回空数组）"
  ]
}}

要求：
1. 必须输出有效的JSON格式，不要有其他文字
2. standard_definition.description必须详细完整（不少于300字）
3. key_points至少3条，每条要具体有信息量
4. use_cases至少2个实际应用场景
5. 所有字符串中的引号用\\"转义
6. 如果没有相关概念或补充，返回空数组[]而不是省略字段
"""

        response = self.llm.generate(prompt, system_prompt)

        if not response:
            return None

        # 解析JSON
        try:
            # 清理可能的markdown代码块标记
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            result = json.loads(response)

            # 验证必需字段
            if 'standard_definition' not in result:
                print("⚠️  警告：JSON中缺少standard_definition字段")
                return None

            return result

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON解析失败: {e}")
            print(f"原始响应: {response[:200]}...")
            return None
