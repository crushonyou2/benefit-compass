package com.benefitcompass.controller;

import com.benefitcompass.dto.AskResponse;
import com.benefitcompass.dto.Policy;
import com.benefitcompass.dto.RecommendRequest;
import com.benefitcompass.service.RagService;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
public class PolicyController {

    private final RagService rag;
    private final MeterRegistry metrics;

    public PolicyController(RagService rag, MeterRegistry metrics) {
        this.rag = rag;
        this.metrics = metrics;
    }

    /** 자격필터 + 의미검색 → 받을 수 있는 정책 목록. */
    @PostMapping("/policies/recommend")
    public List<Policy> recommend(@RequestBody RecommendRequest req) {
        return rag.recommend(req);
    }

    /** 자연어 질문 → 근거 기반 답변 + 근거 정책. */
    @PostMapping("/ask")
    public AskResponse ask(@RequestBody RecommendRequest req) {
        AskResponse response = rag.ask(req);
        String outcome = response.sources().isEmpty() ? "no_results" : "results";
        metrics.counter("benefitcompass.search.requests", "outcome", outcome).increment();
        metrics.summary("benefitcompass.search.result_count").record(response.sources().size());
        return response;
    }
}
