package com.benefitcompass.observability;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

import static org.assertj.core.api.Assertions.assertThat;

class SegmentObservationContextTest {

    @Test
    void springSelectsTheConfiguredConstructor() {
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean(MeterRegistry.class, SimpleMeterRegistry::new);
            context.register(SegmentObservation.class);
            context.refresh();

            assertThat(context.getBean(SegmentObservation.class)).isNotNull();
        }
    }
}
