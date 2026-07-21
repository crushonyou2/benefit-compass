package com.benefitcompass.controller;

import com.benefitcompass.observability.SegmentObservation;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.client.RestClientException;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

/** Converts failures to fixed responses without logging request or downstream body content. */
@RestControllerAdvice
public class ApiExceptionHandler extends ResponseEntityExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);
    private final SegmentObservation segments;

    public ApiExceptionHandler(SegmentObservation segments) {
        this.segments = segments;
    }

    @ExceptionHandler(RestClientException.class)
    ResponseEntity<ApiError> downstreamUnavailable(
            RestClientException exception,
            HttpServletResponse response
    ) {
        return respond(HttpStatus.SERVICE_UNAVAILABLE, "DOWNSTREAM_UNAVAILABLE", exception, response);
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<ApiError> internalError(Exception exception, HttpServletResponse response) {
        return respond(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", exception, response);
    }

    @Override
    protected ResponseEntity<Object> handleExceptionInternal(
            Exception exception,
            Object body,
            HttpHeaders headers,
            HttpStatusCode statusCode,
            WebRequest request
    ) {
        HttpServletResponse response = request instanceof ServletWebRequest servletWebRequest
                ? servletWebRequest.getResponse()
                : null;
        if (response != null && response.isCommitted()) {
            log.warn("api_error_response_committed status={} error_type={}",
                    statusCode.value(), exception.getClass().getSimpleName());
            return null;
        }
        ApiError apiError = observeAndCreateError(
                statusCode.value() >= 500 ? "INTERNAL_ERROR" : "INVALID_REQUEST",
                statusCode.value(),
                exception,
                response);
        return new ResponseEntity<>(apiError, headers, statusCode);
    }

    private ResponseEntity<ApiError> respond(
            HttpStatus status,
            String code,
            Exception exception,
            HttpServletResponse response
    ) {
        ApiError apiError = observeAndCreateError(code, status.value(), exception, response);
        return ResponseEntity.status(status).body(apiError);
    }

    private ApiError observeAndCreateError(
            String code,
            int status,
            Exception exception,
            HttpServletResponse response
    ) {
        String requestId = MDC.get("requestId");
        if (requestId == null) {
            requestId = "none";
        }
        if (status >= 500) {
            log.error("api_error request_id={} status={} error_type={}",
                    requestId, status, exception.getClass().getSimpleName());
        } else {
            log.warn("api_error request_id={} status={} error_type={}",
                    requestId, status, exception.getClass().getSimpleName());
        }
        if (response != null) {
            segments.writeResponseHeaders(response);
        }
        return new ApiError(code, requestId);
    }

    record ApiError(String code, String requestId) {
    }
}
