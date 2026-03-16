import os
import sys
from dotenv import load_dotenv

# 将项目根目录添加到 python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.research_team.graph import analysis_team_graph

def test_research_flow(company_name: str):
    print(f"🚀 开始调研公司: {company_name}...")
    
    # 初始化状态
    inputs = {"company_name": company_name}
    
    # 使用 stream 模式运行，可以观察到每个节点的输出
    try:
        for output in analysis_team_graph.stream(inputs):
            # output 是一个字典，key 是节点名称，value 是该节点返回的 state 更新
            for node_name, state_update in output.items():
                print(f"\n✅ 节点 [{node_name}] 执行完毕")
                if "reference_sources" in state_update:
                    print(f"   已获取参考来源: {len(state_update['reference_sources'])} 条")
        
        # 获取最终结果
        final_state = analysis_team_graph.invoke(inputs)
        print("\n" + "="*50)
        print("📊 最终生成的公司档案 (预览):")
        print("="*50)
        # 只打印前 500 个字符
        print(final_state.get("company_profile", "未生成报告")[:1000] + "...")
        print("="*50)
        
    except Exception as e:
        print(f"❌ 流程执行失败: {e}")

if __name__ == "__main__":
    # 确保你有 API Key
    # os.environ["ANTHROPIC_API_KEY"] = "your_key_here"
    test_research_flow("NVIDIA")
