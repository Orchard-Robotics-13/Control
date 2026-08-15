#include "assignment2/Robot.hpp"
#include <chrono>

AudiCar::AudiCar(std::string id, rclcpp::Node* node) : RobotPlatform(id) 
{
    parent_node_ = node;
    
    gear_pub_ = parent_node_->create_publisher<std_msgs::msg::UInt32>("/audibot/gear_cmd", 10);
    steer_pub_ = parent_node_->create_publisher<std_msgs::msg::Float64>("/audibot/steering_cmd", 10);
    speed_pub_ = parent_node_->create_publisher<std_msgs::msg::Float64>("/audibot/speed_cmd", 10);

    tf_buffer_ = std::make_shared<tf2_ros::Buffer>(parent_node_->get_clock());
    tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

    kp_ = 17.8;
    ki_ = 0.0;
    kd_ = 0.1;
}

double AudiCar::normalizeAngle(double angle) {
    while (angle > M_PI) {
        angle = angle - (2.0 * M_PI);
    }
    while (angle < -M_PI) {
        angle = angle + (2.0 * M_PI);
    }
    return angle;
}

void AudiCar::runMission() 
{
    
    std_msgs::msg::UInt32 gear_msg;
    gear_msg.data = 0; 
    
    std_msgs::msg::Float64 steer_msg;
    std_msgs::msg::Float64 speed_msg;

    //keeping the thread alive because car drifts since speed iis not zero
    while (rclcpp::ok()) {
        
        geometry_msgs::msg::Point current_goal;
        bool has_goal = false;
        
      
        goal_mutex_.lock();
        if (!goal_queue_.empty()) {
            current_goal = goal_queue_.front();
            goal_queue_.pop();
            has_goal = true;
        }
        goal_mutex_.unlock();

        
        if (has_goal == false) {
            speed_msg.data = 0.0;
            steer_msg.data = 0.0;
            
            gear_pub_->publish(gear_msg);
            speed_pub_->publish(speed_msg);
            steer_pub_->publish(steer_msg);
            
            std::this_thread::sleep_for(std::chrono::milliseconds(100)); // 10Hz Idle Loop
            continue; 
        }

        RCLCPP_INFO(parent_node_->get_logger(), "[%s] Navigating to X:%f, Y:%f", platform_id_.c_str(), current_goal.x, current_goal.y);

        bool goal_reached = false;
        double prev_error = 0.0;
        double integral = 0.0;
        double dt = 0.1;

        while (goal_reached == false && rclcpp::ok()) {
            
            geometry_msgs::msg::TransformStamped t;
            try {
                t = tf_buffer_->lookupTransform("world", "base_footprint", tf2::TimePointZero);
            } catch (const tf2::TransformException & ex) {
                std::this_thread::sleep_for(std::chrono::milliseconds(50));
                continue;
            }

            double curr_x = t.transform.translation.x;
            double curr_y = t.transform.translation.y;

            tf2::Quaternion q(t.transform.rotation.x, t.transform.rotation.y, t.transform.rotation.z, t.transform.rotation.w);
            double roll, pitch, curr_yaw;
            tf2::Matrix3x3(q).getRPY(roll, pitch, curr_yaw);

            // Explicit distance calculation
            double diff_x = current_goal.x - curr_x;
            double diff_y = current_goal.y - curr_y;
            double distance = std::hypot(diff_x, diff_y);

            // Check if we hit the 0.5m target radius
            if (distance < 0.5) {
                RCLCPP_INFO(parent_node_->get_logger(), "[%s] Waypoint Reached. Braking.", platform_id_.c_str());
                speed_msg.data = 0.0;
                steer_msg.data = 0.0;
                gear_pub_->publish(gear_msg);
                speed_pub_->publish(speed_msg);
                steer_pub_->publish(steer_msg);
                
                goal_reached = true;
                std::this_thread::sleep_for(std::chrono::milliseconds(1500)); 
                break; // Break the inner loop to grab the next goal (well, kinda)
            }

            // Expanded PID Math
            double targ_yaw = std::atan2(diff_y, diff_x);
            double error = normalizeAngle(targ_yaw - curr_yaw);
            
            integral = integral + (error * dt);
            double derivative = (error - prev_error) / dt;
            double correction = (kp_ * error) + (kd_ * derivative) + (ki_ * integral);
            prev_error = error;

            
            if (correction > 10.68) {
                correction = 10.68;
            } else if (correction < -10.68) {
                correction = -10.68;
            }
            steer_msg.data = correction;

            
            double kv = 0.6;
            double dynamic_speed = distance * kv;
            
            if (dynamic_speed > 6.0) {
                dynamic_speed = 6.0; // Max straight line speed cuz shit starts dying for no reason
            }
            
            // Slow down if making a sharp turn
            if (std::abs(error) > 0.5) {
                if (dynamic_speed > 3.0) {
                    dynamic_speed = 3.0; 
                }
            }
            
            speed_msg.data = dynamic_speed;

            gear_pub_->publish(gear_msg);
            speed_pub_->publish(speed_msg);
            steer_pub_->publish(steer_msg);

            std::this_thread::sleep_for(std::chrono::milliseconds(100)); // 10Hz loop
        }
    }
}