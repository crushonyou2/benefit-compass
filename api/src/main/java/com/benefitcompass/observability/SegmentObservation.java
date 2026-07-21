package com.benefitcompass.observability;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Records fixed-name request segments without user question or age data.
 *
 * <p>The allow lists are intentional: downstream header values cannot create
 * arbitrary metric tags. Per-request values are kept only long enough to emit
 * response timing headers and are removed by {@link RequestObservationFilter}.</p>
 */
@Component
public class SegmentObservation {

    public static final String MODEL_LOAD_HEADER = "X-ML-Model-Load-Ms";
    public static final String SERVER_TIMING_HEADER = "Server-Timing";

    private static final Pattern SERVER_TIMING_ENTRY = Pattern.compile(
            "^([a-z_]+);dur=([0-9]+(?:\\.[0-9]+)?)$");
    private static final Set<String> SEGMENTS = Set.of(
            "api_to_ml", "api_ml_transport", "ml_model_wait", "ml_embedding", "ml_db_connect",
            "ml_db_query", "ml_rerank", "ml_total", "gemini");
    private static final Set<String> OUTCOMES = Set.of("success", "degraded", "error");
    private static final Map<String, String> ML_SEGMENTS = Map.of(
            "model_wait", "ml_model_wait",
            "embedding", "ml_embedding",
            "db_connect", "ml_db_connect",
            "db_query", "ml_db_query",
            "rerank", "ml_rerank",
            "ml_total", "ml_total");

    private final boolean enabled;
    private final Map<String, Map<String, Timer>> timers;
    private final ThreadLocal<RequestTimings> requestTimings = new ThreadLocal<>();

    @Autowired
    public SegmentObservation(
            MeterRegistry metrics,
            @Value("${benefitcompass.observability.segments-enabled:true}") boolean enabled
    ) {
        this.enabled = enabled;
        this.timers = enabled ? createTimers(metrics) : Map.of();
    }

    SegmentObservation(MeterRegistry metrics) {
        this(metrics, true);
    }

    public void beginRequest() {
        if (enabled) {
            requestTimings.set(new RequestTimings());
        }
    }

    public void clearRequest() {
        requestTimings.remove();
    }

    public void recordNanos(String segment, long durationNanos, String outcome) {
        record(segment, durationNanos, TimeUnit.NANOSECONDS, outcome);
    }

    public void recordMillis(String segment, double durationMillis, String outcome) {
        long durationNanos = Math.max(0L, Math.round(durationMillis * 1_000_000.0));
        record(segment, durationNanos, TimeUnit.NANOSECONDS, outcome);
    }

    private void record(String segment, long duration, TimeUnit unit, String outcome) {
        if (!enabled || !SEGMENTS.contains(segment)) {
            return;
        }
        String normalizedOutcome = OUTCOMES.contains(outcome) ? outcome : "error";
        long durationNanos = Math.max(0L, TimeUnit.NANOSECONDS.convert(duration, unit));
        timers.get(segment).get(normalizedOutcome)
                .record(durationNanos, TimeUnit.NANOSECONDS);

        RequestTimings current = requestTimings.get();
        if (current != null) {
            current.durationsMs.put(segment, durationNanos / 1_000_000.0);
        }
    }

    public Double captureMlHeaders(HttpHeaders headers) {
        return captureMlHeaders(headers, "success");
    }

    public Double captureMlHeaders(HttpHeaders headers, String outcome) {
        if (!enabled) {
            return null;
        }
        String normalizedOutcome = OUTCOMES.contains(outcome) ? outcome : "error";
        Double mlTotalMs = null;
        for (String rawEntry : headers.getOrEmpty(SERVER_TIMING_HEADER)) {
            for (String entry : rawEntry.split(",")) {
                Matcher matcher = SERVER_TIMING_ENTRY.matcher(entry.trim());
                if (!matcher.matches()) {
                    continue;
                }
                String segment = ML_SEGMENTS.get(matcher.group(1));
                if (segment != null) {
                    double durationMs = Double.parseDouble(matcher.group(2));
                    recordMillis(segment, durationMs, normalizedOutcome);
                    if ("ml_total".equals(segment)) {
                        mlTotalMs = durationMs;
                    }
                }
            }
        }

        String modelLoad = headers.getFirst(MODEL_LOAD_HEADER);
        if (modelLoad != null && modelLoad.matches("[0-9]+(?:\\.[0-9]+)?")) {
            RequestTimings current = requestTimings.get();
            if (current != null) {
                current.modelLoadMs = Double.parseDouble(modelLoad);
            }
        }
        return mlTotalMs;
    }

    public void writeResponseHeaders(HttpServletResponse response) {
        if (!enabled) {
            return;
        }
        RequestTimings current = requestTimings.get();
        if (current == null) {
            return;
        }
        if (!current.durationsMs.isEmpty()) {
            String value = current.durationsMs.entrySet().stream()
                    .map(entry -> entry.getKey() + ";dur="
                            + String.format(Locale.ROOT, "%.3f", entry.getValue()))
                    .collect(Collectors.joining(", "));
            response.setHeader(SERVER_TIMING_HEADER, value);
        }
        if (current.modelLoadMs != null) {
            response.setHeader(MODEL_LOAD_HEADER,
                    String.format(Locale.ROOT, "%.3f", current.modelLoadMs));
        }
    }

    boolean isEnabled() {
        return enabled;
    }

    private static Map<String, Map<String, Timer>> createTimers(MeterRegistry metrics) {
        Map<String, Map<String, Timer>> result = new HashMap<>();
        for (String segment : SEGMENTS) {
            Map<String, Timer> outcomeTimers = new HashMap<>();
            for (String outcome : OUTCOMES) {
                outcomeTimers.put(outcome, Timer.builder("benefitcompass.segment.duration")
                        .description("Fixed-name request segment latency without user input")
                        .tags("segment", segment, "outcome", outcome)
                        .register(metrics));
            }
            result.put(segment, Map.copyOf(outcomeTimers));
        }
        return Map.copyOf(result);
    }

    private static final class RequestTimings {
        private final Map<String, Double> durationsMs = new LinkedHashMap<>();
        private Double modelLoadMs;
    }
}
