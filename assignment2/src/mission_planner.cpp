#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include <iostream>
#include <thread>
#include <string>

class MissionPlannerNode : public rclcpp::Node {
private:
    rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr mission_pub_;
    
    std::thread* input_thread_;

public:
    MissionPlannerNode() : Node("mission_planner_node") {
        mission_pub_ = this->create_publisher<geometry_msgs::msg::PoseStamped>("/mission/target", 10);
        
        RCLCPP_INFO(this->get_logger(), "Interactive Mission Planner Booted.");

        input_thread_ = new std::thread(&MissionPlannerNode::userInputLoop, this);
    }

    ~MissionPlannerNode() {
        if (input_thread_ != nullptr) {
            if (input_thread_->joinable()) {
                input_thread_->join();
            }
            delete input_thread_;
        }
    }

private:
    void userInputLoop() {
        while (rclcpp::ok()) {
            std::string target_id;
            double x;
            double y;

            std::cout << "\n--- New Fleet Command ---\n";
            std::cout << "Target Vehicle (audi): ";
            std::cin >> target_id;
            
            std::cout << "Target X: ";
            if (!(std::cin >> x)) { 
                std::cin.clear(); 
                std::cin.ignore(10000, '\n'); 
                std::cout << "Invalid input. Numbers only.\n";
                continue; 
            }
            
            std::cout << "Target Y: ";
            if (!(std::cin >> y)) { 
                std::cin.clear(); 
                std::cin.ignore(10000, '\n'); 
                std::cout << "Invalid input. Numbers only.\n";
                continue; 
            }

            geometry_msgs::msg::PoseStamped msg;
            msg.header.stamp = this->get_clock()->now();
            msg.header.frame_id = target_id; 
            msg.pose.position.x = x;
            msg.pose.position.y = y;
            msg.pose.position.z = 0.0;

            mission_pub_->publish(msg);
            RCLCPP_INFO(this->get_logger(), "Dispatched waypoint to [%s]", target_id.c_str());
        }
    }
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MissionPlannerNode>());
    rclcpp::shutdown();
    return 0;
}