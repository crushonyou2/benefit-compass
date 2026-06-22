package com.benefitcompass.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/** 정책 한 건. ML 서비스(snake_case) 역직렬화 + API 응답 직렬화 공용. */
public record Policy(
        @JsonProperty("source_id") String sourceId,
        String title,
        String org,
        @JsonProperty("support_content") String supportContent,
        @JsonProperty("apply_method") String applyMethod,
        @JsonProperty("apply_url") String applyUrl,
        @JsonProperty("age_min") Integer ageMin,
        @JsonProperty("age_max") Integer ageMax,
        @JsonProperty("income_etc") String incomeEtc,
        Double score
) {}
