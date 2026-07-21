package com.benefitcompass.controller;

import com.benefitcompass.dto.Policy;
import com.benefitcompass.observability.RequestObservationFilter;
import com.benefitcompass.observability.SegmentObservation;
import com.benefitcompass.service.RagService;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class PolicyControllerApiTest {

    @Test
    void recommendReturnsPoliciesAndPrivacySafeSegmentHeaders() throws Exception {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        SegmentObservation segments = new SegmentObservation(registry, true);
        RagService rag = mock(RagService.class);
        when(rag.recommend(any())).thenAnswer(invocation -> {
            segments.recordMillis("ml_embedding", 3.5, "success");
            segments.recordMillis("ml_db_query", 7.25, "success");
            segments.recordMillis("api_to_ml", 12.0, "success");
            return List.of(new Policy(
                    "policy-1", "청년 주거 지원", "테스트 기관", "지원 내용",
                    "온라인", "https://example.test", 19, 34, null, 0.9));
        });
        PolicyController controller = new PolicyController(rag, registry, segments);
        MockMvc mvc = MockMvcBuilders.standaloneSetup(controller)
                .addFilters(new RequestObservationFilter(registry, segments))
                .build();

        mvc.perform(post("/api/policies/recommend")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"query\":\"fixed synthetic query\",\"age\":null,\"k\":5}"))
                .andExpect(status().isOk())
                .andExpect(header().exists("X-Request-ID"))
                .andExpect(header().string("Server-Timing",
                        org.hamcrest.Matchers.allOf(
                                org.hamcrest.Matchers.containsString("ml_embedding;dur=3.500"),
                                org.hamcrest.Matchers.containsString("ml_db_query;dur=7.250"),
                                org.hamcrest.Matchers.containsString("api_to_ml;dur=12.000"))))
                .andExpect(jsonPath("$[0].source_id").value("policy-1"));
    }
}
