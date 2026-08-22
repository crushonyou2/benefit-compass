package com.benefitcompass.controller;

import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;
import com.benefitcompass.dto.Policy;
import com.benefitcompass.observability.RequestObservationFilter;
import com.benefitcompass.observability.SegmentObservation;
import com.benefitcompass.service.RagService;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
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

    @Test
    void downstreamFailureReturnsFixedBodyAndStillWritesErrorTimings() throws Exception {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        SegmentObservation segments = new SegmentObservation(registry, true);
        RagService rag = mock(RagService.class);
        when(rag.recommend(any())).thenAnswer(invocation -> {
            segments.recordMillis("ml_model_wait", 10.0, "error");
            segments.recordMillis("ml_total", 10.5, "error");
            segments.recordMillis("api_to_ml", 12.0, "error");
            throw new org.springframework.web.client.RestClientException(
                    "private query 987654321 must not escape");
        });
        PolicyController controller = new PolicyController(rag, registry, segments);
        MockMvc mvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new ApiExceptionHandler(segments))
                .addFilters(new RequestObservationFilter(registry, segments))
                .build();

        Logger handlerLogger = (Logger) LoggerFactory.getLogger(ApiExceptionHandler.class);
        ListAppender<ILoggingEvent> appender = new ListAppender<>();
        appender.start();
        handlerLogger.addAppender(appender);
        ResultActions result;
        try {
            result = mvc.perform(post("/api/policies/recommend")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("{\"query\":\"private query\",\"age\":987654321,\"k\":5}"));
        } finally {
            handlerLogger.detachAppender(appender);
            appender.stop();
        }

        result
                .andExpect(status().isServiceUnavailable())
                .andExpect(header().exists("X-Request-ID"))
                .andExpect(header().string("Server-Timing",
                        org.hamcrest.Matchers.allOf(
                                org.hamcrest.Matchers.containsString("ml_model_wait;dur=10.000"),
                                org.hamcrest.Matchers.containsString("ml_total;dur=10.500"),
                                org.hamcrest.Matchers.containsString("api_to_ml;dur=12.000"))))
                .andExpect(jsonPath("$.code").value("DOWNSTREAM_UNAVAILABLE"))
                .andExpect(jsonPath("$.requestId").isNotEmpty())
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers
                        .content().string(org.hamcrest.Matchers.not(
                                org.hamcrest.Matchers.containsString("private query"))))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers
                        .content().string(org.hamcrest.Matchers.not(
                                org.hamcrest.Matchers.containsString("987654321"))));

        String logs = appender.list.stream()
                .map(ILoggingEvent::getFormattedMessage)
                .collect(java.util.stream.Collectors.joining("\n"));
        org.assertj.core.api.Assertions.assertThat(logs)
                .doesNotContain("private query")
                .doesNotContain("987654321")
                .contains("error_type=RestClientException");
    }

    @Test
    void preservesFrameworkStatusForWrongMethodAndUnsupportedMediaType() throws Exception {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        SegmentObservation segments = new SegmentObservation(registry, true);
        RagService rag = mock(RagService.class);
        PolicyController controller = new PolicyController(rag, registry, segments);
        MockMvc mvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new ApiExceptionHandler(segments))
                .addFilters(new RequestObservationFilter(registry, segments))
                .build();

        mvc.perform(get("/api/policies/recommend"))
                .andExpect(status().isMethodNotAllowed())
                .andExpect(jsonPath("$.code").value("INVALID_REQUEST"));

        mvc.perform(post("/api/policies/recommend")
                        .contentType(MediaType.TEXT_PLAIN)
                        .content("private query 987654321"))
                .andExpect(status().isUnsupportedMediaType())
                .andExpect(jsonPath("$.code").value("INVALID_REQUEST"));

        mvc.perform(post("/api/policies/recommend")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"query\":\"private query 987654321\""))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_REQUEST"))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers
                        .content().string(org.hamcrest.Matchers.not(
                                org.hamcrest.Matchers.containsString("private query"))));

        double clientErrorCount = registry.find("benefitcompass.http.server.duration")
                .tag("status", "4xx").timers().stream()
                .mapToLong(timer -> timer.count()).sum();
        double serverErrorCount = registry.find("benefitcompass.http.server.duration")
                .tag("status", "5xx").timers().stream()
                .mapToLong(timer -> timer.count()).sum();
        org.assertj.core.api.Assertions.assertThat(clientErrorCount).isEqualTo(3.0);
        org.assertj.core.api.Assertions.assertThat(serverErrorCount).isZero();
    }

    @Test
    void rejectsRegionBeforeCallingSearchBecauseRegionDataIsUntrusted() throws Exception {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        SegmentObservation segments = new SegmentObservation(registry, true);
        RagService rag = mock(RagService.class);
        PolicyController controller = new PolicyController(rag, registry, segments);
        MockMvc mvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new ApiExceptionHandler(segments))
                .addFilters(new RequestObservationFilter(registry, segments))
                .build();

        mvc.perform(post("/api/policies/recommend")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"query\":\"fixed synthetic query\",\"region\":\"11\",\"k\":5}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_REQUEST"));

        mvc.perform(post("/api/ask")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"query\":\"fixed synthetic query\",\"region\":\"\",\"k\":5}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_REQUEST"));

        verifyNoInteractions(rag);
    }
}
