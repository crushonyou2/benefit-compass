package com.benefitcompass.client;

import com.benefitcompass.dto.MlResponse;
import com.benefitcompass.dto.Policy;
import com.benefitcompass.dto.RecommendRequest;
import com.benefitcompass.observability.SegmentObservation;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
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
    private final SegmentObservation observation;

    @Autowired
    public MlClient(@Value("${ml.base-url}") String baseUrl, SegmentObservation observation) {
        this(RestClient.builder()
                .baseUrl(baseUrl)
                .requestFactory(new HttpComponentsClientHttpRequestFactory())
                .build(), observation);
    }

    MlClient(RestClient client, SegmentObservation observation) {
        this.client = client;
        this.observation = observation;
    }

    public List<Policy> search(RecommendRequest req) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("query", req.query());
        payload.put("age", req.age());
        payload.put("region", req.region());
        payload.put("k", req.k());

        long startedAt = System.nanoTime();
        String outcome = "error";
        Double mlTotalMs = null;
        try {
            ResponseEntity<MlResponse> entity = client.post()
                    .uri("/search")
                    .headers(headers -> addRequestId(headers, MDC.get("requestId")))
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(payload)
                    .retrieve()
                    .toEntity(MlResponse.class);
            mlTotalMs = observation.captureMlHeaders(entity.getHeaders());
            outcome = "success";
            MlResponse resp = entity.getBody();
            return resp == null ? List.of() : resp.results();
        } finally {
            long roundTripNanos = System.nanoTime() - startedAt;
            observation.recordNanos("api_to_ml", roundTripNanos, outcome);
            if (mlTotalMs != null) {
                double roundTripMs = roundTripNanos / 1_000_000.0;
                observation.recordMillis(
                        "api_ml_transport", Math.max(0.0, roundTripMs - mlTotalMs), outcome);
            }
        }
    }

    private void addRequestId(HttpHeaders headers, String requestId) {
        if (requestId != null && requestId.matches("[A-Za-z0-9-]{1,64}")) {
            headers.set("X-Request-ID", requestId);
        }
    }
}
