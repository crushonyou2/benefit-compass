package com.benefitcompass.observability;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * API 요청을 원문 질문이나 나이 없이 관측한다.
 * endpoint와 status는 제한된 태그만 사용해 메트릭 카디널리티 폭증을 막는다.
 */
@Component
public class RequestObservationFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(RequestObservationFilter.class);
    private static final Set<String> KNOWN_ENDPOINTS = Set.of("/api/ask", "/api/policies/recommend");
    private final MeterRegistry metrics;

    public RequestObservationFilter(MeterRegistry metrics) {
        this.metrics = metrics;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return !request.getRequestURI().startsWith("/api/");
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        String requestId = UUID.randomUUID().toString();
        String endpoint = KNOWN_ENDPOINTS.contains(request.getRequestURI())
                ? request.getRequestURI()
                : "/api/other";
        long startedAt = System.nanoTime();

        response.setHeader("X-Request-ID", requestId);
        MDC.put("requestId", requestId);
        try {
            filterChain.doFilter(request, response);
        } finally {
            long durationNanos = System.nanoTime() - startedAt;
            String statusClass = statusClass(response.getStatus());
            Timer.builder("benefitcompass.http.server.duration")
                    .description("BenefitCompass API latency without user query data")
                    .tags("method", request.getMethod(), "endpoint", endpoint, "status", statusClass)
                    .register(metrics)
                    .record(durationNanos, TimeUnit.NANOSECONDS);
            log.info("api_request method={} endpoint={} status={} duration_ms={}",
                    request.getMethod(), endpoint, response.getStatus(), durationNanos / 1_000_000);
            MDC.remove("requestId");
        }
    }

    private String statusClass(int status) {
        if (status >= 500) return "5xx";
        if (status >= 400) return "4xx";
        if (status >= 300) return "3xx";
        return "2xx";
    }
}
