package com.benefitcompass.client;

import com.benefitcompass.dto.RecommendRequest;
import com.benefitcompass.observability.SegmentObservation;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.ExpectedCount.once;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class MlClientTest {

    @AfterEach
    void clearMdc() {
        MDC.clear();
    }

    @Test
    void propagatesOpaqueRequestIdAndRecordsMlSegments() {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        SegmentObservation observation = new SegmentObservation(registry, true);
        RestClient.Builder builder = RestClient.builder().baseUrl("http://ml.test");
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        server.expect(once(), requestTo("http://ml.test/search"))
                .andExpect(header("X-Request-ID", "request-123"))
                .andRespond(withSuccess("{\"results\":[]}", MediaType.APPLICATION_JSON)
                        .header("Server-Timing",
                                "model_wait;dur=2.0, embedding;dur=4.5, db_connect;dur=3.0, "
                                        + "db_query;dur=6.0, rerank;dur=0.0, ml_total;dur=15.5")
                        .header("X-ML-Model-Load-Ms", "28000.0"));
        MlClient client = new MlClient(builder.build(), observation);

        observation.beginRequest();
        MDC.put("requestId", "request-123");
        assertThat(client.search(new RecommendRequest("synthetic", null, null, 5))).isEmpty();
        server.verify();

        assertThat(registry.get("benefitcompass.segment.duration")
                .tag("segment", "api_to_ml").timer().count()).isEqualTo(1);
        assertThat(registry.get("benefitcompass.segment.duration")
                .tag("segment", "api_ml_transport").timer().count()).isEqualTo(1);
        assertThat(registry.get("benefitcompass.segment.duration")
                .tag("segment", "ml_db_query").timer().totalTime(java.util.concurrent.TimeUnit.MILLISECONDS))
                .isEqualTo(6.0);
        observation.clearRequest();
    }
}
