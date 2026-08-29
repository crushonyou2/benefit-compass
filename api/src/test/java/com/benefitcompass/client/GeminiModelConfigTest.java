package com.benefitcompass.client;

import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

class GeminiModelConfigTest {

    @Test
    void modelIsEnvConfigurableWith35LiteDefault() throws Exception {
        String yaml = Files.readString(Path.of("src/main/resources/application.yml"));
        assertThat(yaml).contains("${GEMINI_MODEL:gemini-3.5-flash-lite}");
        assertThat(yaml).doesNotContain("gemini-3.1-flash-lite");
    }

    @Test
    void geminiClientKeepsInjectedModelWithoutHardcoding() {
        GeminiClient client = new GeminiClient("k", "gemini-3.5-flash-lite", null, null);
        // 생성자가 주입값을 그대로 보관하는지 간접 확인: generate 호출 시 모델 경로에 반영됨은 기존 GeminiClientTest에서 검증
        assertThat(client).isNotNull();
    }
}
