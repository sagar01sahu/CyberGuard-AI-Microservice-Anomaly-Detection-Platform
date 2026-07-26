package com.security.anomalydetection.repository;

import com.security.anomalydetection.entity.AccessLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AccessLogRepository extends JpaRepository<AccessLog, Long> {


    List<AccessLog> findTop5ByEntityIdOrderByTimestampDesc(String entityId);


    List<AccessLog> findTop50ByProcessingStatusOrderByTimestampAsc(String processingStatus);
}
