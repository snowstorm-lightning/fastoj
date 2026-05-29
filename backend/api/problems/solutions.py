
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.services.problem_service import ProblemService
from backend.services.solution_service import SolutionService

router = APIRouter(prefix="/problems/{problem_id}/solutions", tags=["solutions"])

ZH_EXPLANATIONS = {
    "two-sum": "遍历数组时用哈希表保存已经见过的值和下标。对每个元素只需要检查 target - nums[i] 是否已经出现，因此可以在线性时间内找到答案。",
    "add-two-numbers": "按位模拟竖式加法，同时维护进位。两个输入数组表示逆序数字，遍历到较长数组结束且进位为 0 时停止。",
    "longest-substring-without-repeating": "使用滑动窗口维护当前无重复子串。右指针扩张窗口，遇到重复字符时把左边界移动到上次出现位置之后。",
    "valid-parentheses": "用栈保存尚未匹配的左括号。遇到右括号时检查栈顶类型是否匹配，最后栈为空才是合法括号串。",
    "logistic-regression-sigmoid": "先计算线性得分 w·x+b，再通过 sigmoid 转成概率。实现时可以对极大或极小输入做稳定处理，避免指数溢出。",
    "knn-majority-vote": "计算查询点到每个训练点的欧氏距离，取最近的 k 个样本投票。票数相同时按标签字典序稳定返回。",
    "kmeans-one-iteration": "固定当前聚类中心，对每个样本计算到所有中心的距离，并分配给最近中心。这里只实现一次分配步骤，不更新中心。",
    "scaled-dot-product-attention": "先计算 query 与每个 key 的点积并除以 sqrt(d)，再做稳定 softmax 得到权重，最后用权重加权 value 向量。",
    "softmax-cross-entropy": "对 logits 减去最大值后计算 softmax，取目标类别概率的负对数作为交叉熵损失。",
    "attention-mask-apply": "先把 mask 为 0 的位置排除在 softmax 之外，只在可见位置归一化概率，被屏蔽位置输出 0。",
    "maximum-subarray": "使用 Kadane 算法维护以当前位置结尾的最大子数组和，同时更新全局最优答案。",
    "group-anagrams": "互为字母异位词的字符串排序后键相同。按这个键分组，再对组内和组间做稳定排序，得到确定输出。",
    "merge-intervals": "先按区间左端点排序。新区间和结果末尾重叠时合并右端点，否则开启一个新区间。",
    "climbing-stairs": "到达第 n 阶的方法数等于到达第 n-1 阶和第 n-2 阶的方法数之和，可用滚动变量维护。",
    "container-with-most-water": "用双指针从两端开始计算面积。面积受较短边限制，因此每次移动较短边尝试找到更优解。",
}

ZH_EXPLANATIONS["longest-substring-without-repeating-characters"] = ZH_EXPLANATIONS[
    "longest-substring-without-repeating"
]


@router.get("")
async def get_problem_solutions(
    problem_id: str,
    language: str | None = None,
    locale: str = "zh",
    db: Session = Depends(get_db),
):
    """Get solutions for a problem."""
    # Verify problem exists
    problem_service = ProblemService(db)
    problem = problem_service.get_problem_by_id(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    solution_service = SolutionService(db)
    solutions = solution_service.get_solutions(problem_id, language)

    def explanation_for(value: str) -> str:
        if locale == "zh":
            return ZH_EXPLANATIONS.get(problem.slug, value)
        return value

    return {
        "success": True,
        "data": [
            {
                "id": str(s.id),
                "language": s.language,
                "code": s.code,
                "explanation": explanation_for(s.explanation),
                "time_complexity": s.time_complexity,
                "space_complexity": s.space_complexity,
            }
            for s in solutions
        ],
    }
