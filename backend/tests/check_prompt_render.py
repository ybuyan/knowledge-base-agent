import sys
sys.path.insert(0, 'backend')

from app.prompts.manager import prompt_manager

print("=" * 60)
print("检查 Prompt 渲染")
print("=" * 60)

context = """[1] [Page 40]
（5）坚持业余自学，不断提高业务水平，在公司任职期间，获取硕士以上文凭
或其他专业高级以上职称和证书者；
（6）具有其他功绩，总经理认为应给予晋级者。
4、其他维护公司利益和名誉,为公司创造利润和价值的行为，有事实证明者，
亦予以奖励。
5、公司员工具有上述各项情况并取得相应奖励时，经公司经理办公会议批准，
可单独或同时给予 100-1000元人民币奖金。
6.总经理特别奖励，由总经理根据公司员工的功绩确定,给予不同程度奖励。
第五条   奖励换算
员工一年内累计嘉奖 3次等于记功 1次,累计记功 3次可奖励晋级一档工资。
第六条   奖励程序
员工符合奖励条件者，由所在部门主管提名,填写《员工奖励申请表》，报人力资源部审核,由总经理批准后执行。

[2] [Page 39]
（2）领导有方，使业务工作拓展有相当成效者；
（3）品行端正，遵守规章、服从领导，堪为全体员工楷模者；
（4）厉行节约，或利用废料有显著成绩者；
（5）工作积极、忠于职守、出色完成工作任务者；
（6）具有其他功绩，总经理认为应给予晋级者。
4、其他维护公司利益和名誉,为公司创造利润和价值的行为，有事实证明者，
亦予以奖励。
"""

question = "公司有哪些福利？"

print(f"\n上下文长度: {len(context)}")
print(f"问题: {question}")

print(f"\n渲染 Prompt...")
prompts = prompt_manager.render("qa_rag", {
    "context": context,
    "question": question
})

print(f"\nSystem Prompt:")
print(prompts["system"])

print(f"\nUser Prompt:")
print(prompts["user"])

print("\n" + "=" * 60)
