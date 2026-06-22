package com.benefitcompass.dto;

/** 프론트 → API 요청. ML 서비스 /search 와 필드명이 일치한다. */
public record RecommendRequest(String query, Integer age, String region, Integer k) {
    public RecommendRequest {
        if (k == null) k = 5;
    }
}
