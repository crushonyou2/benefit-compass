package com.benefitcompass.observability;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.springframework.mock.web.MockHttpServletResponse;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Local microbenchmark for the incremental segment-observation code.
 * It never creates request DTOs, so question and age data cannot enter its CSV.
 */
public final class ObservationOverheadBenchmark {

    private static final int WARMUP_OPERATIONS = 50_000;
    private static final int OPERATIONS = 50_000;
    private static final int ROUNDS = 9;

    private ObservationOverheadBenchmark() {
    }

    public static void main(String[] args) throws IOException {
        if (args.length != 1) {
            throw new IllegalArgumentException("expected one output CSV path");
        }
        Path output = Path.of(args[0]).toAbsolutePath().normalize();
        SegmentObservation enabled = new SegmentObservation(new SimpleMeterRegistry(), true);
        SegmentObservation disabled = new SegmentObservation(new SimpleMeterRegistry(), false);

        run(enabled, WARMUP_OPERATIONS);
        run(disabled, WARMUP_OPERATIONS);

        List<String> rows = new ArrayList<>();
        rows.add("timestamp_utc,round,mode,operations,total_ns,ns_per_operation");
        for (int round = 1; round <= ROUNDS; round++) {
            SegmentObservation first = round % 2 == 0 ? disabled : enabled;
            SegmentObservation second = round % 2 == 0 ? enabled : disabled;
            String firstMode = round % 2 == 0 ? "disabled" : "enabled";
            String secondMode = round % 2 == 0 ? "enabled" : "disabled";
            rows.add(row(round, firstMode, run(first, OPERATIONS)));
            rows.add(row(round, secondMode, run(second, OPERATIONS)));
        }

        Files.createDirectories(output.getParent());
        Files.write(output, rows, StandardCharsets.UTF_8);
        System.out.printf(Locale.ROOT,
                "observation overhead raw CSV: %s (%d rounds, %d operations/mode/round)%n",
                output, ROUNDS, OPERATIONS);
    }

    private static long run(SegmentObservation observation, int operations) {
        long startedAt = System.nanoTime();
        for (int i = 0; i < operations; i++) {
            observation.beginRequest();
            observation.recordMillis("ml_model_wait", 0.01, "success");
            observation.recordMillis("ml_embedding", 8.0, "success");
            observation.recordMillis("ml_db_connect", 20.0, "success");
            observation.recordMillis("ml_db_query", 4.0, "success");
            observation.recordMillis("ml_total", 32.01, "success");
            observation.recordMillis("api_to_ml", 35.0, "success");
            observation.recordMillis("api_ml_transport", 2.99, "success");
            observation.writeResponseHeaders(new MockHttpServletResponse());
            observation.clearRequest();
        }
        return System.nanoTime() - startedAt;
    }

    private static String row(int round, String mode, long totalNanos) {
        double nanosPerOperation = (double) totalNanos / OPERATIONS;
        return String.format(Locale.ROOT, "%s,%d,%s,%d,%d,%.3f",
                Instant.now(), round, mode, OPERATIONS, totalNanos, nanosPerOperation);
    }
}
