# Stage 1: Build the application using Maven
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY . .
# Use global 'mvn' instead of './mvnw' since Maven is pre-installed in this image
RUN mvn clean package -DskipTests

# Stage 2: Run the application
FROM eclipse-temurin:17-jre-jammy
WORKDIR /app

# Copy the built jar from the build stage and rename it to app.jar
COPY --from=build /app/target/*.jar app.jar

# Entrypoint to handle Render's database URL and start the app
ENTRYPOINT ["sh", "-c", "export SPRING_DATASOURCE_URL=\"jdbc:postgresql://${DATABASE_URL#*://}?sslmode=require\"; exec java -jar app.jar"]