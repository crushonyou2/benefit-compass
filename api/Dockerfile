# --- build stage (JDK 17, Gradle wrapper) ---
FROM eclipse-temurin:17-jdk AS build
WORKDIR /app
COPY . .
RUN chmod +x ./gradlew && ./gradlew clean bootJar -x test --no-daemon

# --- run stage (JRE 17) ---
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /app/build/libs/*.jar app.jar
# Cloud Run이 PORT를 주입 → application.yml의 server.port=${PORT:8080}가 처리
CMD ["java", "-jar", "app.jar"]
