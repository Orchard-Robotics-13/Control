#ifndef ROBOT_HPP
#define ROBOT_HPP

#include <string>
#include <queue>
#include <thread>
#include <mutex>
#include <cmath>
#include <iostream>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/point.hpp"
#include "std_msgs/msg/u_int32.hpp"
#include "std_msgs/msg/float64.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"

#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2/LinearMath/Matrix3x3.h"


class RobotPlatform {
protected:
    std::string platform_id_;
    std::queue<geometry_msgs::msg::Point> goal_queue_;
    std::mutex goal_mutex_;
    std::thread* control_thread_; 
    bool mission_active_;

public:
   
    RobotPlatform(std::string id) {
        platform_id_ = id;
        mission_active_ = false;
        control_thread_ = nullptr; 
    }

    
    virtual ~RobotPlatform() {
        mission_active_ = false;
        if (control_thread_ != nullptr) {
            if (control_thread_->joinable()) {
                control_thread_->join();
            }
            delete control_thread_;
        }
    }

    std::string getId() { 
        return platform_id_; 
    }

    void addGoal(geometry_msgs::msg::Point target) {
        goal_mutex_.lock();
        goal_queue_.push(target);
        goal_mutex_.unlock(); 

     
        if (mission_active_ == false) {
            mission_active_ = true;
            
          
            if (control_thread_ != nullptr) {
                if (control_thread_->joinable()) {
                    control_thread_->join();
                }
                delete control_thread_;
            }
            
            
            control_thread_ = new std::thread(&RobotPlatform::runMission, this);
        }
    }

    
    virtual void runMission() = 0;
};

class AudiCar : public RobotPlatform {
private:
    rclcpp::Node* parent_node_; 
    
   
    rclcpp::Publisher<std_msgs::msg::UInt32>::SharedPtr gear_pub_;
    rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr steer_pub_;
    rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr speed_pub_;
    
    std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_;

    double kp_;
    double kd_;
    double ki_;

public:
    AudiCar(std::string id, rclcpp::Node* node);
    void runMission() override;
    double normalizeAngle(double angle);
};

class HuskyRobot : public RobotPlatform {
private:
    rclcpp::Node* parent_node_;
    
    // Updated Interfaces
    rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr cmd_vel_pub_;
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;

    // Odometry Callback
    void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg);

    // Thread-safe state variables
    std::mutex state_mutex_;
    double current_x_;
    double current_y_;
    double current_yaw_;

    // PID constants
    double kp_angular_;
    double kd_angular_;
    double kp_linear_;

public:
    HuskyRobot(std::string id, rclcpp::Node* node);
    void runMission() override;
    double normalizeAngle(double angle);
};

#endif