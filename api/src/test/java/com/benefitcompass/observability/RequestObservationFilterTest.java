package com.benefitcompass.observability;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class RequestObservationFilterTest {

    @Test
    void recordsOnlyNormalizedEndpointAndStatusTags() throws Exception {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        RequestObservationFilter filter = new RequestObservationFilter(
                registry, new SegmentObservation(registry));
        MockHttpServletRequest request = new MockHttpServletRequest("POST", "/api/ask");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilter(request, response, (req, res) -> ((MockHttpServletResponse) res).setStatus(200));

        // The ML service drops anything that is not a canonical UUIDv4 and logs request_id=none,
        // so a regression in this generator would silently break the cross-service trace.
        String requestId = response.getHeader("X-Request-ID");
        assertThat(requestId).isNotBlank();
        UUID parsed = UUID.fromString(requestId);
        assertThat(parsed.version()).isEqualTo(4);
        assertThat(parsed.toString()).isEqualTo(requestId);
        assertThat(registry.get("benefitcompass.http.server.duration")
                .tag("method", "POST")
                .tag("endpoint", "/api/ask")
                .tag("status", "2xx")
                .timer().count()).isEqualTo(1);
    }

    @Test
    void collapsesUnknownApiPathsToPreventHighCardinality() throws Exception {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        RequestObservationFilter filter = new RequestObservationFilter(
                registry, new SegmentObservation(registry));
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/arbitrary-user-value");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilter(request, response, (req, res) -> ((MockHttpServletResponse) res).setStatus(404));

        assertThat(registry.get("benefitcompass.http.server.duration")
                .tag("endpoint", "/api/other")
                .tag("status", "4xx")
                .timer().count()).isEqualTo(1);
    }
}
