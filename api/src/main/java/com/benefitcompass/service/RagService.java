package com.benefitcompass.service;

import com.benefitcompass.client.GeminiClient;
import com.benefitcompass.client.MlClient;
import com.benefitcompass.dto.AskResponse;
import com.benefitcompass.dto.Policy;
import com.benefitcompass.dto.RecommendRequest;
import org.springframework.stereotype.Service;

import java.util.List;

/** RAG 오케스트레이션: ML 검색 → 프롬프트 구성 → Gemini 답변. */
@Service
public class RagService {

    private final MlClient ml;
    private final GeminiClient gemini;

    public RagService(MlClient ml, GeminiClient gemini) {
        this.ml = ml;
        this.gemini = gemini;
    }

    /** 자격필터 + 의미검색으로 정책 목록만 반환 (리스트 화면용). */
    public List<Policy> recommend(RecommendRequest req) {
        return ml.search(req);
    }

    /** 검색 결과를 근거로 자연어 답변 생성 (Q&A). */
    public AskResponse ask(RecommendRequest req) {
        List<Policy> policies = ml.search(req);
        if (policies.isEmpty()) {
            return new AskResponse(
                    "딱 맞는 정책을 바로 찾지는 못했어요. 검색어를 조금 바꿔 다시 시도해 보세요. "
                    + "(관련 정책이 있어도 검색이 놓쳤을 수 있어요.)", List.of());
        }
        String answer = gemini.generate(buildPrompt(req.query(), policies));
        return new AskResponse(answer, policies);
    }

    private String buildPrompt(String question, List<Policy> policies) {
        StringBuilder ctx = new StringBuilder();
        for (Policy p : policies) {
            String age = p.ageMin() != null ? p.ageMin() + "~" + p.ageMax() + "세" : "연령무관";
            String support = p.supportContent() == null ? ""
                    : p.supportContent().replaceAll("\\s+", " ").trim();
            if (support.length() > 120) support = support.substring(0, 120) + "…";
            ctx.append("- ").append(p.title()).append(" (").append(p.org())
               .append(", ").append(age)
               .append(p.incomeEtc() != null ? ", " + p.incomeEtc() : "").append("): ")
               .append(support).append("\n");
        }
        return """
                너는 정부 지원금 안내 도우미다. 아래 [정책 목록]만 근거로 답해라.

                규칙:
                - 2~3문장으로 짧고 친근하게. 상세는 화면 카드에 이미 있으니 나열하지 마라.
                - 마크다운(**, #, -)을 절대 쓰지 말고 평범한 문장으로.
                - 가장 적합한 정책 1~2개 이름을 언급하되, "없다"고 단정하지 마라.
                - 질문과 딱 맞는 정책이 안 보이면, "딱 맞는 건 바로 찾지 못했지만 아래 정책이 참고될 수 있어요"처럼
                  부드럽게 안내하고 검색어를 바꿔보라고 권해라. (관련 정책이 있어도 검색이 놓쳤을 수 있으니 단정 금지)

                [사용자 질문]
                %s

                [정책 목록]
                %s

                [답변]""".formatted(question, ctx.toString());
    }
}
