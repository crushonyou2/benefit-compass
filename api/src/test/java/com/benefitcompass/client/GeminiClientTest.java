package com.benefitcompass.client;

import com.benefitcompass.observability.SegmentObservation;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.ExpectedCount.once;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class GeminiClientTest {

    @Test
    void recordsGeminiDurationWithoutPromptMetricTags() {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        SegmentObservation observation = new SegmentObservation(registry, true);
        RestClient.Builder builder = RestClient.builder().baseUrl("https://gemini.test/v1beta");
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        server.expect(once(), requestTo(
                        "https://gemini.test/v1beta/models/test-model:generateContent"))
                .andRespond(withSuccess(
                        "{\"candidates\":[{\"content\":{\"parts\":[{\"text\":\"safe answer\"}]}}]}",
                        MediaType.APPLICATION_JSON));
        GeminiClient client = new GeminiClient(
                "test-key", "test-model", builder.build(), observation);

        observation.beginRequest();
        assertThat(client.generate("synthetic prompt")).isEqualTo("safe answer");
        server.verify();

        assertThat(registry.get("benefitcompass.segment.duration")
                .tag("segment", "gemini")
                .tag("outcome", "success")
                .timer().count()).isEqualTo(1);
        assertThat(registry.getMeters()).allSatisfy(meter ->
                assertThat(meter.getId().getTags()).allSatisfy(tag ->
                        assertThat(tag.getValue()).doesNotContain("synthetic prompt")));
        observation.clearRequest();
    }
}
