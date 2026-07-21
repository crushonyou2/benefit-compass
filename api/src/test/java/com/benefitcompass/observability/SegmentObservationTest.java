package com.benefitcompass.observability;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.mock.web.MockHttpServletResponse;

import static org.assertj.core.api.Assertions.assertThat;

class SegmentObservationTest {

    @Test
    void acceptsOnlyFixedMlSegmentsAndEmitsNoUserData() {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        SegmentObservation observation = new SegmentObservation(registry);
        HttpHeaders headers = new HttpHeaders();
        headers.add("Server-Timing",
                "embedding;dur=12.5, db_query;dur=4.25, raw_question;dur=999");
        headers.set(SegmentObservation.MODEL_LOAD_HEADER, "30123.5");

        observation.beginRequest();
        observation.captureMlHeaders(headers);
        observation.recordMillis("api_to_ml", 20.0, "success");
        MockHttpServletResponse response = new MockHttpServletResponse();
        observation.writeResponseHeaders(response);

        assertThat(response.getHeader("Server-Timing"))
                .contains("ml_embedding;dur=12.500")
                .contains("ml_db_query;dur=4.250")
                .contains("api_to_ml;dur=20.000")
                .doesNotContain("raw_question");
        assertThat(response.getHeader(SegmentObservation.MODEL_LOAD_HEADER))
                .isEqualTo("30123.500");
        assertThat(registry.get("benefitcompass.segment.duration")
                .tag("segment", "ml_embedding").timer().count()).isEqualTo(1);
        assertThat(registry.getMeters()).allSatisfy(meter ->
                assertThat(meter.getId().getTags()).allSatisfy(tag ->
                        assertThat(tag.getValue())
                                .doesNotContain("raw question")
                                .doesNotContain("31")));
        observation.clearRequest();
    }

    @Test
    void disabledObservationWritesNoSegmentHeadersOrMeters() {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        SegmentObservation observation = new SegmentObservation(registry, false);
        observation.beginRequest();
        observation.recordMillis("api_to_ml", 20.0, "success");
        MockHttpServletResponse response = new MockHttpServletResponse();
        observation.writeResponseHeaders(response);

        assertThat(response.getHeader("Server-Timing")).isNull();
        assertThat(registry.getMeters()).isEmpty();
    }
}
