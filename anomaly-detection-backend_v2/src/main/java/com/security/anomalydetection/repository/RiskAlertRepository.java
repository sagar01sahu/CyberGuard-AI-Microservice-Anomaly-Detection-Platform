package com.security.anomalydetection.repository;

import com.security.anomalydetection.entity.RiskAlert;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface RiskAlertRepository extends JpaRepository<RiskAlert, Long> {


    List<RiskAlert> findTop20ByOrderByTimestampDesc();
}
