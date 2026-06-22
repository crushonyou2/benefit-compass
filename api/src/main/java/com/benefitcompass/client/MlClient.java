package com.benefitcompass.client;

import com.benefitcompass.dto.MlResponse;
import com.benefitcompass.dto.Policy;
import com.benefitcompass.dto.RecommendRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Python ML/검색 서비스(/search) 호출. */
@Component
public class MlClient {

    private final RestClient client;

    public MlClient(@Value("${ml.base-url}") String baseUrl) {
        this.client = RestClient.builder()
                .baseUrl(baseUrl)
                .requestFactory(new HttpComponentsClientHttpRequestFactory())
                .build();
    }

    public List<Policy> search(RecommendRequest req) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("query", req.query());
        payload.put("age", req.age());
        payload.put("region", req.region());
        payload.put("k", req.k());

        MlResponse resp = client.post()
                .uri("/search")
                .contentType(MediaType.APPLICATION_JSON)
                .body(payload)
                .retrieve()
                .body(MlResponse.class);
        return resp == null ? List.of() : resp.results();
    }
}
