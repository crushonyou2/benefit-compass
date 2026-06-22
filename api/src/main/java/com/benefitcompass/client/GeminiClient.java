package com.benefitcompass.client;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import java.util.List;
import java.util.Map;

/** Gemini generateContent 호출 (답변 생성). 503/429 과부하 시 백오프 재시도. */
@Component
public class GeminiClient {

    private static final int MAX_ATTEMPTS = 3;

    private final RestClient client;
    private final String apiKey;
    private final String model;

    public GeminiClient(@Value("${gemini.api-key}") String apiKey,
                        @Value("${gemini.model}") String model) {
        this.apiKey = apiKey;
        this.model = model;
        this.client = RestClient.builder()
                .baseUrl("https://generativelanguage.googleapis.com/v1beta")
                .requestFactory(new HttpComponentsClientHttpRequestFactory())
                .build();
    }

    public String generate(String prompt) {
        Map<String, Object> body = Map.of(
                "contents", List.of(Map.of("parts", List.of(Map.of("text", prompt)))));

        for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
            try {
                JsonNode resp = client.post()
                        .uri("/models/{model}:generateContent", model)
                        .header("x-goog-api-key", apiKey)
                        .contentType(MediaType.APPLICATION_JSON)
                        .body(body)
                        .retrieve()
                        .body(JsonNode.class);
                if (resp == null) {
                    return "답변 생성에 실패했어요.";
                }
                return resp.at("/candidates/0/content/parts/0/text").asText("답변 생성에 실패했어요.");
            } catch (RestClientResponseException e) {
                int sc = e.getStatusCode().value();
                boolean transient_ = (sc == 503 || sc == 429 || sc == 500);
                if (transient_ && attempt < MAX_ATTEMPTS) {
                    sleep(1500L * attempt);
                    continue;
                }
                if (transient_) {
                    return "지금 답변 생성 요청이 많아요. 잠시 후 다시 시도해 주세요. (아래 정책 목록은 참고하세요.)";
                }
                throw e;
            }
        }
        return "답변 생성에 실패했어요.";
    }

    private void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
