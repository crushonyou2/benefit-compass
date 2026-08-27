package com.benefitcompass.service;

import com.benefitcompass.client.GeminiClient;
import com.benefitcompass.client.MlClient;
import com.benefitcompass.dto.AskResponse;
import com.benefitcompass.dto.Policy;
import com.benefitcompass.dto.RecommendRequest;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class RagServiceTest {

    @Test
    void noSearchResultsDoNotCallGemini() {
        MlClient ml = mock(MlClient.class);
        GeminiClient gemini = mock(GeminiClient.class);
        RecommendRequest request = new RecommendRequest("없는 지원", null, null, 5);
        when(ml.search(request)).thenReturn(List.of());

        AskResponse response = new RagService(ml, gemini).ask(request);

        assertThat(response.sources()).isEmpty();
        assertThat(response.answer()).contains("찾지는 못했어요");
        verifyNoInteractions(gemini);
    }

    @Test
    void promptContainsOnlyRetrievedPoliciesWithTheirSourcesAndLinks() {
        MlClient ml = mock(MlClient.class);
        GeminiClient gemini = mock(GeminiClient.class);
        RecommendRequest request = new RecommendRequest("생활비 지원", null, null, 5);
        List<Policy> policies = List.of(
                new Policy("gov24", "g-1", "생활안정 지원", "행정안전부", "지원 내용",
                        "온라인", "https://www.gov.kr/example", null, null, null, 0.9),
                new Policy("youth", "y-1", "청년 생활비 지원", "온통청년", "청년 지원 내용",
                        "방문", "https://www.youthcenter.go.kr/example", 19, 34, null, 0.8));
        when(ml.search(request)).thenReturn(policies);
        when(gemini.generate(org.mockito.ArgumentMatchers.anyString())).thenReturn("근거 답변");

        AskResponse response = new RagService(ml, gemini).ask(request);

        ArgumentCaptor<String> prompt = ArgumentCaptor.forClass(String.class);
        verify(gemini).generate(prompt.capture());
        assertThat(prompt.getValue())
                .contains("생활안정 지원", "청년 생활비 지원", "출처: 정부24", "출처: 온통청년")
                .contains("https://www.gov.kr/example");
        assertThat(response.sources()).containsExactlyElementsOf(policies);
    }
}
