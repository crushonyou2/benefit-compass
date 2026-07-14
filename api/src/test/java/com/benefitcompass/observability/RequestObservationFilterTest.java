package com.benefitcompass.observability;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import static org.assertj.core.api.Assertions.assertThat;

class RequestObservationFilterTest {

    @Test
    void recordsOnlyNormalizedEndpointAndStatusTags() throws Exception {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        RequestObservationFilter filter = new RequestObservationFilter(registry);
        MockHttpServletRequest request = new MockHttpServletRequest("POST", "/api/ask");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilter(request, response, (req, res) -> ((MockHttpServletResponse) res).setStatus(200));

        assertThat(response.getHeader("X-Request-ID")).isNotBlank();
        assertThat(registry.get("benefitcompass.http.server.duration")
                .tag("method", "POST")
                .tag("endpoint", "/api/ask")
                .tag("status", "2xx")
                .timer().count()).isEqualTo(1);
    }

    @Test
    void collapsesUnknownApiPathsToPreventHighCardinality() throws Exception {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        RequestObservationFilter filter = new RequestObservationFilter(registry);
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/arbitrary-user-value");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilter(request, response, (req, res) -> ((MockHttpServletResponse) res).setStatus(404));

        assertThat(registry.get("benefitcompass.http.server.duration")
                .tag("endpoint", "/api/other")
                .tag("status", "4xx")
                .timer().count()).isEqualTo(1);
    }
}
