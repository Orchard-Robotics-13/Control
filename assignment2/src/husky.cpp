#include "assignment2/Robot.hpp"
#include <chrono>

HuskyRobot::HuskyRobot(std::string id, rclcpp::Node* node) : RobotPlatform(id), 
    current_x_(0.0), current_y_(0.0), current_yaw_(0.0)
{
    parent_node_ = node;
    

    cmd_vel_pub_ = parent_node_->create_publisher<geometry_msgs::msg::TwistStamped>("/a300_00000/cmd_vel", 10);
    
    odom_sub_ = parent_node_->create_subscription<nav_msgs::msg::Odometry>(
        "/a300_00000/platform/odom", 10,
        std::bind(&HuskyRobot::odomCallback, this, std::placeholders::_1)
    );

    kp_angular_ = 1.5;
    kd_angular_ = 0.1;
    kp_linear_ = 0.5;
}

void HuskyRobot::odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg) {

    std::lock_guard<std::mutex> lock(state_mutex_);
    
    current_x_ = msg->pose.pose.position.x;
    current_y_ = msg->pose.pose.position.y;
    
    tf2::Quaternion q(
        msg->pose.pose.orientation.x,
        msg->pose.pose.orientation.y,
        msg->pose.pose.orientation.z,
        msg->pose.pose.orientation.w
    );
    double roll, pitch, yaw;
    tf2::Matrix3x3(q).getRPY(roll, pitch, yaw);
    current_yaw_ = yaw;
}

double HuskyRobot::normalizeAngle(double angle) {
    while (angle > M_PI) angle -= (2.0 * M_PI);
    while (angle < -M_PI) angle += (2.0 * M_PI);
    return angle;
}

void HuskyRobot::runMission() 
{
    geometry_msgs::msg::TwistStamped twist_msg;
    twist_msg.header.frame_id = "a300_00000/base_link";

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

        if (!has_goal) {
            twist_msg.header.stamp = parent_node_->get_clock()->now();
            twist_msg.twist.linear.x = 0.0;
            twist_msg.twist.angular.z = 0.0;
            cmd_vel_pub_->publish(twist_msg);
            
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            continue; 
        }

        RCLCPP_INFO(parent_node_->get_logger(), "[%s] Navigating to X:%f, Y:%f", platform_id_.c_str(), current_goal.x, current_goal.y);

        bool goal_reached = false;
        double prev_error = 0.0;

        while (!goal_reached && rclcpp::ok()) {
            

            double curr_x, curr_y, curr_yaw;
            {
                std::lock_guard<std::mutex> lock(state_mutex_);
                curr_x = current_x_;
                curr_y = current_y_;
                curr_yaw = current_yaw_;
            }


            double diff_x = current_goal.x - curr_x;
            double diff_y = current_goal.y - curr_y;
            

            double dist = std::hypot(diff_x, diff_y); 


            if (dist < 0.5) {
                RCLCPP_INFO(parent_node_->get_logger(), "[%s] Waypoint Reached.", platform_id_.c_str());
                
                // Stop the robot
                twist_msg.twist.linear.x = 0.0;
                twist_msg.twist.angular.z = 0.0;
                twist_msg.header.stamp = parent_node_->get_clock()->now();
                cmd_vel_pub_->publish(twist_msg);
                
                goal_reached = true;
                break;

            }

            double target_yaw = std::atan2(diff_y, diff_x);



            double error = normalizeAngle(target_yaw - curr_yaw);


            double derivative = error - prev_error;
            double correction = (kp_angular_ * error) + (kd_angular_ * derivative);
            prev_error = error;



            if (std::abs(error) > 0.2) {
                twist_msg.twist.angular.z = correction;
                twist_msg.twist.linear.x = 0.0;
            } else {

                twist_msg.twist.angular.z = correction;
                

                double target_speed = dist * kp_linear_;
                twist_msg.twist.linear.x = std::min(target_speed, 1.0); 
            }


            twist_msg.header.stamp = parent_node_->get_clock()->now();
            cmd_vel_pub_->publish(twist_msg);

            std::this_thread::sleep_for(std::chrono::milliseconds(100)); // 10Hz loop
        }
    }
}
