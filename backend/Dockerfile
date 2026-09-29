# ---- Build stage: Maven + JDK 17 (matches pom.xml java.version=17) ----
FROM maven:3.9-eclipse-temurin-17-alpine AS build
WORKDIR /app

# Leverage layer caching: dependencies first
COPY pom.xml ./
COPY src ./src
RUN mvn -B clean package -DskipTests

# ---- Runtime stage: smallest JRE that runs Java 17 ----
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

# Run as non-root is not possible with default alpine images without extra setup;
# keep minimal: only the built jar, no Maven, no source, no build tools.
COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

# Spring Boot picks up SPRING_DATASOURCE_URL / USERNAME / PASSWORD env vars
# to override application.properties (which still points at localhost for local dev).
ENTRYPOINT ["java", "-jar", "app.jar"]
