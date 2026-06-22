package com.benefitcompass.dto;

import java.util.List;

/** ML 서비스 /search 응답 래퍼. */
public record MlResponse(List<Policy> results) {}
