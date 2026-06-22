package com.benefitcompass.dto;

import java.util.List;

/** Q&A 응답: 근거 기반 답변 + 근거가 된 정책 목록. */
public record AskResponse(String answer, List<Policy> sources) {}
